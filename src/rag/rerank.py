"""Local cross-encoder reranker for RAG results."""

import logging

from sentence_transformers import CrossEncoder

from src.config.settings import settings

logger = logging.getLogger(__name__)

_model: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        logger.info("Loading cross-encoder model: %s", settings.cross_encoder_model)
        _model = CrossEncoder(settings.cross_encoder_model)
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
