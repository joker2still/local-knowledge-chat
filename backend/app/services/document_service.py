from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_store import upsert_chunks


BASE_DATA_DIR = Path("backend/data")
RAW_DATA_DIR = BASE_DATA_DIR / "raw"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def ingest_text_file(file: UploadFile) -> dict:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    content = file.file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Only UTF-8 encoded .txt files are supported") from exc

    if not text.strip():
        raise ValueError("Uploaded file is empty")

    raw_file_path = RAW_DATA_DIR / file.filename
    raw_file_path.write_bytes(content)

    chunks = split_text(text)
    if not chunks:
        raise ValueError("Uploaded file has no valid text chunks")

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
                    "source": file.filename,
                    "chunk_id": chunk_id,
                    "text": chunk,
                },
            }
        )

    upsert_chunks(points, vector_size=vector_size)

    return {
        "filename": file.filename,
        "chunks": len(points),
        "vector_store": "qdrant_local",
    }


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
