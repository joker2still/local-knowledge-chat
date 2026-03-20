import json
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.app.services.embedding_service import generate_embedding


BASE_DATA_DIR = Path("backend/data")
RAW_DATA_DIR = BASE_DATA_DIR / "raw"
PROCESSED_DATA_DIR = BASE_DATA_DIR / "processed"
CHUNKS_FILE = PROCESSED_DATA_DIR / "chunks.json"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def ingest_text_file(file: UploadFile) -> dict:
    _ensure_data_dirs()

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
    chunk_records = []

    for index, chunk in enumerate(chunks):
        chunk_records.append(
            {
                "id": str(uuid4()),
                "filename": file.filename,
                "chunk_index": index,
                "text": chunk,
                "embedding": generate_embedding(chunk),
            }
        )

    existing_records = _load_existing_chunks()
    existing_records.extend(chunk_records)
    CHUNKS_FILE.write_text(
        json.dumps(existing_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "filename": file.filename,
        "chunks": len(chunk_records),
        "output_file": str(CHUNKS_FILE),
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


def load_chunks() -> list[dict]:
    return _load_existing_chunks()


def _ensure_data_dirs() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_existing_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        return []

    return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
