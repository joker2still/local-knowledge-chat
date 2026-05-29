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


def list_document_stats() -> list[dict[str, Any]]:
    if count_chunks() == 0:
        return []

    client = _client()
    offset: models.PointId | None = None
    documents: dict[str, dict[str, Any]] = {}

    while True:
        try:
            points, next_offset = client.scroll(
                collection_name=settings.qdrant_collection,
                limit=256,
                with_payload=True,
                with_vectors=False,
                offset=offset,
            )
        except Exception as exc:
            logger.exception("Failed to list qdrant documents")
            raise ExternalServiceError("Failed to list documents from Qdrant") from exc

        for point in points:
            payload = point.payload or {}
            source = str(payload.get("source", "")).strip()
            if not source:
                continue

            file_type = str(payload.get("file_type", "")).strip()
            page_number = payload.get("page_number")

            if source not in documents:
                documents[source] = {
                    "filename": source,
                    "file_type": file_type,
                    "chunks": 0,
                    "page_numbers": set(),
                }

            documents[source]["chunks"] += 1
            if page_number is not None:
                documents[source]["page_numbers"].add(int(page_number))

        if next_offset is None:
            break
        offset = next_offset

    return [
        {
            "filename": item["filename"],
            "file_type": item["file_type"],
            "chunks": item["chunks"],
            "page_count": len(item["page_numbers"]),
        }
        for item in sorted(documents.values(), key=lambda value: value["filename"].lower())
    ]


def list_chunks_by_source(source: str) -> list[dict[str, Any]]:
    if not source or count_chunks_by_source(source) == 0:
        return []

    client = _client()
    offset: models.PointId | None = None
    chunks: list[dict[str, Any]] = []

    while True:
        try:
            points, next_offset = client.scroll(
                collection_name=settings.qdrant_collection,
                limit=256,
                with_payload=True,
                with_vectors=False,
                offset=offset,
                scroll_filter=_source_filter(source),
            )
        except Exception as exc:
            logger.exception("Failed to list qdrant chunks by source")
            raise ExternalServiceError("Failed to list document chunks from Qdrant") from exc

        for point in points:
            payload = point.payload or {}
            text = str(payload.get("text", ""))
            chunks.append(
                {
                    "chunk_id": str(payload.get("chunk_id", point.id)),
                    "source": str(payload.get("source", source)),
                    "page_number": payload.get("page_number"),
                    "file_type": str(payload.get("file_type", "")),
                    "text": text,
                    "preview": text[:200],
                }
            )

        if next_offset is None:
            break
        offset = next_offset

    return sorted(
        chunks,
        key=lambda item: (
            item["page_number"] if item["page_number"] is not None else -1,
            item["chunk_id"],
        ),
    )


def count_chunks_by_source(source: str) -> int:
    client = _client()
    try:
        result = client.count(
            collection_name=settings.qdrant_collection,
            count_filter=_source_filter(source),
            exact=True,
        )
    except Exception:
        return 0
    return int(result.count)


def delete_chunks_by_source(source: str) -> int:
    deleted_chunks = count_chunks_by_source(source)
    if deleted_chunks == 0:
        return 0

    client = _client()
    try:
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=models.FilterSelector(filter=_source_filter(source)),
        )
    except Exception as exc:
        logger.exception("Failed to delete chunks by source")
        raise ExternalServiceError("Failed to delete document vectors from Qdrant") from exc

    return deleted_chunks


def clear_collection() -> int:
    deleted_chunks = count_chunks()
    if deleted_chunks == 0:
        return 0

    client = _client()
    try:
        client.delete_collection(collection_name=settings.qdrant_collection)
    except Exception as exc:
        logger.exception("Failed to delete qdrant collection")
        raise ExternalServiceError("Failed to clear Qdrant collection") from exc

    return deleted_chunks


def _source_filter(source: str) -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key="source",
                match=models.MatchValue(value=source),
            )
        ]
    )
