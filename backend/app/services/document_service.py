import logging
from io import BytesIO
from uuid import uuid4

from fastapi import UploadFile
from pypdf import PdfReader

from backend.app.core.config import settings
from backend.app.core.exceptions import AppError
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_store import upsert_chunks


logger = logging.getLogger(__name__)


def ingest_text_file(file: UploadFile) -> dict:
    filename = file.filename or ""
    file_type = get_file_type(filename)
    if file_type not in {"txt", "pdf"}:
        raise AppError(message="Only .txt and .pdf files are supported", code="invalid_file_type", status_code=400)

    content = file.file.read()

    settings.raw_data_dir_obj.mkdir(parents=True, exist_ok=True)
    raw_file_path = settings.raw_data_dir_obj / filename
    raw_file_path.write_bytes(content)

    logger.info("file_uploaded filename=%s size_bytes=%s file_type=%s", filename, len(content), file_type)

    segments = extract_segments(content=content, file_type=file_type)
    if not segments:
        raise AppError(message="Uploaded file has no valid text content", code="empty_file", status_code=400)

    points = []
    vector_size = 0
    chunk_count = 0

    chunk_inputs = build_chunk_inputs(segments=segments, file_type=file_type)
    for page_number, chunk in chunk_inputs:
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
                    "page_number": page_number,
                    "file_type": file_type,
                },
            }
        )
        chunk_count += 1

    if not points:
        raise AppError(message="Uploaded file has no valid text chunks", code="no_chunks", status_code=400)

    logger.info("chunks_created filename=%s chunk_count=%s file_type=%s", filename, chunk_count, file_type)
    logger.info("embeddings_generated filename=%s chunk_count=%s", filename, chunk_count)

    upsert_chunks(points, vector_size=vector_size)
    logger.info("chunks_upserted filename=%s chunk_count=%s", filename, chunk_count)

    return {
        "filename": filename,
        "chunks": chunk_count,
        "vector_store": "qdrant_local",
    }


def get_file_type(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".txt"):
        return "txt"
    if lowered.endswith(".pdf"):
        return "pdf"
    return ""


def extract_segments(content: bytes, file_type: str) -> list[tuple[int | None, str]]:
    if file_type == "txt":
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AppError(message="Only UTF-8 encoded .txt files are supported", code="invalid_encoding", status_code=400) from exc
        return [(None, text)] if text.strip() else []

    if file_type == "pdf":
        try:
            reader = PdfReader(BytesIO(content))
        except Exception as exc:
            raise AppError(message="Failed to parse PDF file", code="pdf_parse_error", status_code=400) from exc

        segments: list[tuple[int | None, str]] = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                segments.append((index, page_text))
        return segments

    return []


def build_chunk_inputs(segments: list[tuple[int | None, str]], file_type: str) -> list[tuple[int | None, str]]:
    if file_type == "txt":
        return [(None, chunk) for _, text in segments for chunk in split_text(text)]

    if file_type == "pdf":
        return split_pdf_text(segments)

    return []


def split_pdf_text(segments: list[tuple[int | None, str]]) -> list[tuple[int | None, str]]:
    size = settings.upload_chunk_size
    overlap_size = settings.upload_chunk_overlap
    step = max(size - overlap_size, 1)

    page_ranges: list[tuple[int, int, int | None]] = []
    full_text_parts: list[str] = []
    cursor = 0

    for page_number, text in segments:
        normalized_text = normalize_pdf_text(text)
        if not normalized_text:
            continue
        if full_text_parts:
            full_text_parts.append(" ")
            cursor += 1
        start = cursor
        full_text_parts.append(normalized_text)
        cursor += len(normalized_text)
        end = cursor
        page_ranges.append((start, end, page_number))

    full_text = "".join(full_text_parts)
    if not full_text:
        return []

    chunk_inputs: list[tuple[int | None, str]] = []
    start = 0
    while start < len(full_text):
        end = start + size
        chunk = full_text[start:end].strip()
        if chunk:
            chunk_inputs.append((find_page_number(start, page_ranges), chunk))
        start += step

    return chunk_inputs


def normalize_pdf_text(text: str) -> str:
    return " ".join(text.split())


def find_page_number(position: int, page_ranges: list[tuple[int, int, int | None]]) -> int | None:
    for start, end, page_number in page_ranges:
        if start <= position < end:
            return page_number
    return page_ranges[-1][2] if page_ranges else None


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
