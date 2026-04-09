import logging
from uuid import uuid4

from fastapi import UploadFile

from backend.app.core.config import settings
from backend.app.core.exceptions import AppError
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_store import upsert_chunks


logger = logging.getLogger(__name__)


def ingest_text_file(file: UploadFile) -> dict:
    filename = file.filename or ""
    if not filename.endswith(".txt"):
        raise AppError(message="Only .txt files are supported", code="invalid_file_type", status_code=400)

    content = file.file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AppError(message="Only UTF-8 encoded .txt files are supported", code="invalid_encoding", status_code=400) from exc

    if not text.strip():
        raise AppError(message="Uploaded file is empty", code="empty_file", status_code=400)

    settings.raw_data_dir_obj.mkdir(parents=True, exist_ok=True)
    raw_file_path = settings.raw_data_dir_obj / filename
    raw_file_path.write_bytes(content)

    logger.info("file_uploaded filename=%s size_bytes=%s", filename, len(content))

    chunks = split_text(text)
    if not chunks:
        raise AppError(message="Uploaded file has no valid text chunks", code="no_chunks", status_code=400)

    logger.info("chunks_created filename=%s chunk_count=%s", filename, len(chunks))

    points = []
    vector_size = 0

    for chunk in chunks:
        chunk_id = str(uuid4())
        embedding = generate_embedding(chunk)
        if vector_size == 0:
            vector_size = len(embedding)
        points.append(
            {
                "id": chunk_id,
                "vector": embedding,
                "payload": {
                    "source": filename,
                    "chunk_id": chunk_id,
                    "text": chunk,
                },
            }
        )

    logger.info("embeddings_generated filename=%s chunk_count=%s", filename, len(points))
    upsert_chunks(points, vector_size=vector_size)
    logger.info("chunks_upserted filename=%s chunk_count=%s", filename, len(points))

    return {
        "filename": filename,
        "chunks": len(points),
        "vector_store": "qdrant_local",
    }


def split_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    size = chunk_size or settings.upload_chunk_size
    overlap_size = overlap or settings.upload_chunk_overlap
    step = max(size - overlap_size, 1)

    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
