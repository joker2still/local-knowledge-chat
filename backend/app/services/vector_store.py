from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models


QDRANT_PATH = Path("backend/data/qdrant")
COLLECTION_NAME = "knowledge_base"


def _client() -> QdrantClient:
    QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_PATH))


def ensure_collection(vector_size: int) -> None:
    client = _client()
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
    except Exception:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )


def upsert_chunks(points: list[dict[str, Any]], vector_size: int) -> None:
    if not points:
        return

    ensure_collection(vector_size)
    client = _client()
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(id=point["id"], vector=point["vector"], payload=point["payload"])
            for point in points
        ],
    )


def search_chunks(query_vector: list[float], limit: int = 3) -> list[dict[str, Any]]:
    if count_chunks() == 0:
        return []

    ensure_collection(len(query_vector))
    client = _client()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
    )

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
        result = client.count(collection_name=COLLECTION_NAME, exact=True)
    except Exception:
        return 0
    return int(result.count)
