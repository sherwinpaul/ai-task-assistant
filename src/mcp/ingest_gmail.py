"""Fetch Gmail messages, normalize, and upsert into ChromaDB."""

import json
import logging

from src.mcp.google_mcp_server import gmail_search_messages
from src.mcp.normalize import normalize_gmail
from src.rag.retriever import upsert_documents

logger = logging.getLogger(__name__)


def ingest_gmail(query: str = "is:inbox", max_results: int = 50) -> int:
    """Fetch Gmail messages and ingest into ChromaDB.

    Returns:
        Number of documents upserted.
    """
    logger.info("Starting Gmail ingestion (query=%s, max=%d)", query, max_results)
    raw_json = gmail_search_messages.invoke(
        {"query": query, "max_results": max_results}
    )
    messages = json.loads(raw_json)
    tasks = [normalize_gmail(msg) for msg in messages]
    count = upsert_documents(tasks)
    logger.info("Gmail ingestion complete: %d documents", count)
    return count
