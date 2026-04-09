import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from backend.app.core.config import settings
from backend.app.core.exceptions import ExternalServiceError


logger = logging.getLogger(__name__)


def _client() -> QdrantClient:
    settings.qdrant_path_obj.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(settings.qdrant_path_obj))


def ensure_collection(vector_size: int) -> None:
    client = _client()
    try:
        client.get_collection(collection_name=settings.qdrant_collection)
        return
    except Exception:
        pass

    try:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        logger.info("qdrant_collection_created collection=%s vector_size=%s", settings.qdrant_collection, vector_size)
    except Exception as exc:
        logger.exception("Failed to create qdrant collection")
        raise ExternalServiceError("Failed to initialize Qdrant collection") from exc


def upsert_chunks(points: list[dict[str, Any]], vector_size: int) -> None:
    if not points:
        return

    ensure_collection(vector_size)
    client = _client()
    try:
        client.upsert(
            collection_name=settings.qdrant_collection,
            points=[
                models.PointStruct(id=point["id"], vector=point["vector"], payload=point["payload"])
                for point in points
            ],
        )
    except Exception as exc:
        logger.exception("Failed to upsert chunks")
        raise ExternalServiceError("Failed to upsert vectors into Qdrant") from exc


def search_chunks(query_vector: list[float], limit: int | None = None) -> list[dict[str, Any]]:
    if count_chunks() == 0:
        return []

    top_k = limit or settings.retrieval_top_k
    ensure_collection(len(query_vector))

    client = _client()
    try:
        results = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )
    except Exception as exc:
        logger.exception("Failed to query qdrant")
        raise ExternalServiceError("Failed to search vectors from Qdrant") from exc

    return [
        {
            "id": str(item.id),
            "score": float(item.score),
            "payload": item.payload or {},
        }
        for item in results.points
    ]


def count_chunks() -> int:
    client = _client()
    try:
        result = client.count(collection_name=settings.qdrant_collection, exact=True)
    except Exception:
        return 0
    return int(result.count)
