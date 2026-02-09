"""Fetch Jira issues, normalize, and upsert into ChromaDB."""

import json
import logging

from src.mcp.jira_mcp_server import jira_list_issues
from src.mcp.normalize import normalize_jira
from src.rag.retriever import upsert_documents

logger = logging.getLogger(__name__)


def ingest_jira(project_key: str = "", max_results: int = 100) -> int:
    """Fetch Jira issues and ingest into ChromaDB.

    Returns:
        Number of documents upserted.
    """
    logger.info("Starting Jira ingestion (project=%s, max=%d)", project_key, max_results)
    raw_json = jira_list_issues.invoke(
        {"project_key": project_key, "max_results": max_results}
    )
    issues = json.loads(raw_json)
    tasks = [normalize_jira(issue) for issue in issues]
    count = upsert_documents(tasks)
    logger.info("Jira ingestion complete: %d documents", count)
    return count
