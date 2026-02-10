"""ChromaDB persistent client for vector storage and retrieval."""

import logging

import chromadb

from src.config.settings import settings
from src.schemas.task_schema import TaskSchema

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None
COLLECTION_NAME = "tasks"


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert_documents(tasks: list[TaskSchema]) -> int:
    """Upsert a list of TaskSchema objects into ChromaDB. Returns count upserted."""
    if not tasks:
        return 0

    collection = get_collection()
    ids = [t.id for t in tasks]
    documents = [t.to_document_text() for t in tasks]
    metadatas = [
        {
            "source": t.source,
            "title": t.title,
            "status": t.status or "",
            "priority": t.priority or "",
            "assignee": t.assignee or "",
            "url": t.url or "",
        }
        for t in tasks
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    count = collection.count()
    logger.info("Upserted %d documents into ChromaDB (total: %d)", len(ids), count)
    return len(ids)


def retrieve(query: str, top_k: int | None = None, max_distance: float = 0.80) -> list[dict]:
    """Query ChromaDB and return top_k results as dicts with id, document, metadata, distance.

    Args:
        query: The search query.
        top_k: Maximum number of results to return.
        max_distance: Cosine distance threshold — docs above this are filtered out
                      as irrelevant (lower = stricter, 0.80 balances recall vs noise).
    """
    if top_k is None:
        top_k = settings.retrieval_top_k

    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    effective_k = min(top_k, count)
    results = collection.query(query_texts=[query], n_results=effective_k)

    documents = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i] if results.get("distances") else None
        # Filter out docs that are too far from the query in embedding space
        if distance is not None and distance > max_distance:
            continue
        documents.append(
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": distance,
            }
        )
    return documents
