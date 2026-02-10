"""Chat pipeline: cache -> guardrail -> RAG -> rerank -> Gemini (fast path) or Agent (tool path)."""

import logging
import re
import time
from datetime import datetime, timezone

from google import genai
from google.genai import types as genai_types
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.prompts import (
    FAST_SYSTEM_PROMPT,
    RAG_TEMPLATE,
    REFUSAL_PROMPT,
    SYSTEM_PROMPT,
    check_write_intent,
)
from src.config.settings import gemini_key_rotator, settings
from src.mcp.google_mcp_server import get_google_tools
from src.mcp.jira_mcp_server import get_jira_tools
from src.rag.cache import (
    get_cached_response,
    get_cached_retrieval,
    set_cached_response,
    set_cached_retrieval,
)
from src.rag.rerank import rerank
from src.rag.retriever import retrieve
from src.reminders.scheduler import get_reminder_tools

logger = logging.getLogger(__name__)

# --- Keyword routing ---
# Keywords that need the agent (tool calls) AND live API data (skip RAG)
# Use action-oriented phrases to avoid false positives on broad nouns.
_AGENT_KEYWORDS = re.compile(
    r"\b(remind|reminder|set a reminder|search jira|search gmail|search calendar|"
    r"look up|find issue|find issues|search for|my issues|my tickets|"
    r"unread emails?|unread|inbox|check gmail|check my email|"
    r"upcoming events?|upcoming meetings?|next meeting|my calendar|check calendar|"
    r"show me|list my|do i have)\b",
    re.IGNORECASE,
)

# Broad questions answered well by RAG context alone (fast path)
# These used to hit the agent path unnecessarily.
_RAG_SUFFICIENT_KEYWORDS = re.compile(
    r"\b(summarize|prioritize|overview|status of|what should i|work on next|"
    r"what are my tasks|my tasks|overdue|due this week|due today)\b",
    re.IGNORECASE,
)

# Cached agent executors — keyed by API key to avoid rebuilding
_agent_cache: dict[str, AgentExecutor] = {}

# Cached Gemini clients for the fast path (one per API key — no global state)
_genai_client_cache: dict[str, genai.Client] = {}
_genai_gen_config: genai_types.GenerateContentConfig | None = None


def _needs_agent(message: str) -> bool:
    """Return True only if the query genuinely needs live tool calls.

    Broad questions like 'summarize my tasks' or 'prioritize my work' are
    better served by RAG context and the fast Gemini path.
    """
    if _RAG_SUFFICIENT_KEYWORDS.search(message):
        return False
    return bool(_AGENT_KEYWORDS.search(message))


def _get_genai_client(api_key: str) -> genai.Client:
    """Return a cached google.genai Client for the given API key."""
    if api_key not in _genai_client_cache:
        _genai_client_cache[api_key] = genai.Client(api_key=api_key)
    return _genai_client_cache[api_key]


def _get_gen_config() -> genai_types.GenerateContentConfig:
    """Return the shared generation config (created once)."""
    global _genai_gen_config
    if _genai_gen_config is None:
        _genai_gen_config = genai_types.GenerateContentConfig(
            temperature=settings.temperature,
            top_p=settings.top_p,
            max_output_tokens=512,
        )
    return _genai_gen_config


def _fast_gemini_call(prompt: str) -> str:
    """Direct Gemini API call via google.genai — much faster than LangChain agent."""
    api_key = gemini_key_rotator.next()
    client = _get_genai_client(api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=_get_gen_config(),
        )
        return response.text or ""
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return "I'm temporarily unable to process your request due to rate limits. Please try again in a moment."


def get_agent_executor() -> AgentExecutor:
    """Return a cached AgentExecutor, rebuilding only when a new API key is seen."""
    api_key = gemini_key_rotator.next()
    if api_key in _agent_cache:
        return _agent_cache[api_key]

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=api_key,
        temperature=settings.temperature,
        top_p=settings.top_p,
        max_output_tokens=1024,
        timeout=10,
    )

    tools = get_jira_tools() + get_google_tools() + get_reminder_tools()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + "\n\nCurrent time: {current_time}"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=3,
        max_execution_time=15,
    )
    _agent_cache[api_key] = executor
    return executor


def process_message(message: str, chat_history: list | None = None) -> dict:
    """Full pipeline: cache -> guardrail -> RAG -> rerank -> LLM.

    Uses fast direct Gemini call for simple RAG queries.
    Falls back to full LangChain agent only when tool calls are needed.
    Agent queries always skip RAG (they get fresh data from tools).
    """
    t0 = time.perf_counter()

    # 0. Short-circuit empty/whitespace messages (BUG-5)
    stripped = message.strip()
    if not stripped:
        return {
            "response": "It looks like your message was empty. How can I help you with your tasks, emails, or calendar?",
            "sources": [],
            "cached": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # 1. Response cache check (includes chat history in key)
    cached = get_cached_response(message, chat_history)
    if cached is not None:
        cached["cached"] = True
        logger.info("Cache hit — %.1fms", (time.perf_counter() - t0) * 1000)
        return cached

    # 2. Write-request guardrail
    blocked_action = check_write_intent(message)
    if blocked_action:
        response = {
            "response": REFUSAL_PROMPT.format(action=blocked_action),
            "sources": [],
            "cached": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        set_cached_response(message, response, chat_history)
        return response

    use_agent = _needs_agent(message)
    t_route = time.perf_counter()

    # 3. RAG retrieval — skip for agent queries (they get fresh data from tools)
    rag_docs = []
    sources = []
    if not use_agent:
        rag_docs = get_cached_retrieval(message)
        if rag_docs is None:
            t_ret = time.perf_counter()
            rag_docs = retrieve(message)
            logger.info("  retrieve: %.0fms (%d docs)", (time.perf_counter() - t_ret) * 1000, len(rag_docs))
            set_cached_retrieval(message, rag_docs)

        # 4. Local reranking
        if rag_docs:
            t_rr = time.perf_counter()
            rag_docs = rerank(message, rag_docs)
            logger.info("  rerank: %.0fms (%d docs)", (time.perf_counter() - t_rr) * 1000, len(rag_docs))

        sources = [
            {"id": doc["id"], "source": doc["metadata"].get("source", ""), "title": doc["metadata"].get("title", "")}
            for doc in rag_docs
        ]

    # 5. Build context
    context = "\n\n---\n\n".join(doc["document"] for doc in rag_docs) if rag_docs else "No relevant context found in the knowledge base."

    # 6. Choose fast path or agent path
    if use_agent:
        augmented_input = message
        executor = get_agent_executor()
        t_llm = time.perf_counter()
        try:
            result = executor.invoke({
                "input": augmented_input,
                "chat_history": chat_history or [],
                "current_time": datetime.now(timezone.utc).isoformat(),
            })
            raw_output = result.get("output", "")
            if isinstance(raw_output, list):
                raw_output = "\n".join(
                    block.get("text", str(block)) if isinstance(block, dict) else str(block)
                    for block in raw_output
                )
            # Guard against None or empty agent output
            if not raw_output or not raw_output.strip():
                raw_output = "I wasn't able to retrieve that information right now. Please try rephrasing your request or being more specific."
                logger.warning("Agent returned empty output for: %s", message[:80])
        except Exception as e:
            logger.error("Agent execution failed: %s", e, exc_info=True)
            raw_output = "Something went wrong while processing your request. Please try again."
        logger.info("  agent: %.0fms", (time.perf_counter() - t_llm) * 1000)
    else:
        # Fast direct Gemini call — shorter prompt, no agent overhead
        now = datetime.now(timezone.utc).isoformat()
        full_prompt = f"{FAST_SYSTEM_PROMPT}\nCurrent time: {now}\n\n{RAG_TEMPLATE.format(context=context, question=message)}"
        t_llm = time.perf_counter()
        raw_output = _fast_gemini_call(full_prompt)
        logger.info("  gemini: %.0fms (%d chars)", (time.perf_counter() - t_llm) * 1000, len(raw_output or ""))

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("Total: %.0fms | path=%s | query=%s", elapsed, "agent" if use_agent else "fast", message[:60])

    response = {
        "response": raw_output,
        "sources": sources,
        "cached": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 7. Cache response (includes chat history in key)
    set_cached_response(message, response, chat_history)
    return response
