"""FastAPI entry point with /chat, /ingest, /cache/clear, and /health endpoints."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent.router import process_message
from src.mcp.ingest_calendar import ingest_calendar
from src.mcp.ingest_gmail import ingest_gmail
from src.mcp.ingest_jira import ingest_jira
from src.rag.cache import clear_all_caches
from src.rag.rerank import get_reranker
from src.reminders.models import get_engine
from src.reminders.scheduler import get_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting AI Task Assistant...")
    get_engine()  # Initialize DB
    get_scheduler()  # Start APScheduler
    get_reranker()  # Pre-load cross-encoder model

    # Auto-ingest all sources into ChromaDB on startup
    for name, fn in [("jira", ingest_jira), ("gmail", ingest_gmail), ("calendar", ingest_calendar)]:
        try:
            count = fn()
            logger.info("Auto-ingested %s: %d documents", name, count)
        except Exception as e:
            logger.warning("Auto-ingest %s failed (non-fatal): %s", name, e)

    # Warmup: prime ChromaDB embeddings + Gemini client so first user query is fast
    try:
        from src.rag.retriever import retrieve
        retrieve("warmup query")
        logger.info("Warmup retrieval complete")
    except Exception as e:
        logger.warning("Warmup failed (non-fatal): %s", e)

    yield
    scheduler = get_scheduler()
    scheduler.shutdown(wait=False)
    logger.info("AI Task Assistant shut down.")


app = FastAPI(
    title="AI Task Management Assistant",
    description="Read-only AI assistant for Jira, Gmail, and Google Calendar with RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---


class ChatRequest(BaseModel):
    message: str
    chat_history: list[dict] | None = None


class ChatResponse(BaseModel):
    response: str
    sources: list[dict]
    cached: bool
    timestamp: str


class IngestRequest(BaseModel):
    sources: list[str] | None = None  # ["jira", "gmail", "calendar"] or None for all


class IngestResponse(BaseModel):
    results: dict[str, int | str]


# --- Endpoints ---


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the RAG + agent pipeline."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await asyncio.to_thread(
            process_message, request.message, request.chat_history
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest | None = None):
    """Ingest data from external sources into ChromaDB."""
    sources = (request.sources if request and request.sources else ["jira", "gmail", "calendar"])
    results: dict[str, int | str] = {}

    for source in sources:
        try:
            if source == "jira":
                results["jira"] = ingest_jira()
            elif source == "gmail":
                results["gmail"] = ingest_gmail()
            elif source == "calendar":
                results["calendar"] = ingest_calendar()
            else:
                results[source] = "unknown source"
        except Exception as e:
            logger.error("Ingestion error for %s: %s", source, e, exc_info=True)
            results[source] = f"error: {e}"

    return IngestResponse(results=results)


@app.post("/cache/clear")
async def cache_clear():
    """Clear all retrieval and response caches."""
    clear_all_caches()
    return {"status": "caches cleared"}
