"""Local cross-encoder reranker for RAG results."""

import logging
import os
import time

from sentence_transformers import CrossEncoder

from src.config.settings import settings

logger = logging.getLogger(__name__)

_model: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        t0 = time.perf_counter()
        logger.info("Loading cross-encoder model: %s", settings.cross_encoder_model)
        # Use local cache only — skip HuggingFace hub checks for faster startup
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        _model = CrossEncoder(settings.cross_encoder_model)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("Cross-encoder loaded in %.0fms", elapsed)
    return _model


def rerank(query: str, documents: list[dict], top_n: int | None = None) -> list[dict]:
    """Rerank retrieved documents using a cross-encoder.

    Args:
        query: The user query.
        documents: List of dicts with at least a "document" key.
        top_n: Number of top results to return.

    Returns:
        Top-N documents sorted by relevance score (descending).
    """
    if top_n is None:
        top_n = settings.rerank_top_n

    if not documents:
        return []

    model = get_reranker()
    pairs = [(query, doc["document"]) for doc in documents]
    scores = model.predict(pairs)

    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    ranked = sorted(documents, key=lambda d: d["rerank_score"], reverse=True)
    return ranked[:top_n]
