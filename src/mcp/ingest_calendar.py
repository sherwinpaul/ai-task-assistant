"""Fetch Google Calendar events, normalize, and upsert into ChromaDB."""

import json
import logging

from src.mcp.google_mcp_server import gcal_list_events
from src.mcp.normalize import normalize_calendar
from src.rag.retriever import upsert_documents

logger = logging.getLogger(__name__)


def ingest_calendar(days_ahead: int = 30, max_results: int = 50) -> int:
    """Fetch upcoming calendar events and ingest into ChromaDB.

    Returns:
        Number of documents upserted.
    """
    logger.info("Starting Calendar ingestion (days=%d, max=%d)", days_ahead, max_results)
    raw_json = gcal_list_events.invoke(
        {"days_ahead": days_ahead, "max_results": max_results}
    )
    events = json.loads(raw_json)
    tasks = [normalize_calendar(evt) for evt in events]
    count = upsert_documents(tasks)
    logger.info("Calendar ingestion complete: %d documents", count)
    return count
