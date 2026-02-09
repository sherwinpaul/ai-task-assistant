"""Dual TTL caches for retrieval results and chat responses."""

import hashlib
import json
import logging

from cachetools import TTLCache

from src.config.settings import settings

logger = logging.getLogger(__name__)

retrieval_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.retrieval_cache_ttl)
response_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.response_cache_ttl)


def _make_key(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


def _make_response_key(query: str, chat_history: list | None = None) -> str:
    """Build cache key from query + chat history so context-dependent answers aren't stale."""
    raw = query.strip().lower()
    if chat_history:
        raw += json.dumps(chat_history, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached_retrieval(query: str) -> list[dict] | None:
    key = _make_key(query)
    result = retrieval_cache.get(key)
    if result is not None:
        logger.debug("Retrieval cache hit for query: %s", query[:50])
    return result


def set_cached_retrieval(query: str, documents: list[dict]) -> None:
    key = _make_key(query)
    retrieval_cache[key] = documents


def get_cached_response(query: str, chat_history: list | None = None) -> dict | None:
    key = _make_response_key(query, chat_history)
    result = response_cache.get(key)
    if result is not None:
        logger.debug("Response cache hit for query: %s", query[:50])
    return result


def set_cached_response(query: str, response: dict, chat_history: list | None = None) -> None:
    key = _make_response_key(query, chat_history)
    response_cache[key] = response


def clear_all_caches() -> None:
    retrieval_cache.clear()
    response_cache.clear()
    logger.info("All caches cleared")
