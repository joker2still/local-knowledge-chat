from pathlib import Path

from backend.app.core.config import settings
from backend.app.services.llm_service import generate_response
from backend.app.services.vector_store import (
    delete_chunks_by_source,
    list_chunks_by_source,
    list_document_stats,
)


def list_documents() -> dict:
    documents = list_document_stats()
    if documents:
        return {
            "documents": documents,
        }

    raw_dir = settings.raw_data_dir_obj
    if not raw_dir.exists():
        return {"documents": []}

    names = sorted(
        file.name
        for file in raw_dir.iterdir()
        if file.is_file()
    )
    return {
        "documents": names,
    }


def get_document_chunks(doc_id: str) -> dict:
    if not doc_id:
        return {
            "doc_id": "",
            "chunk_count": 0,
            "chunks": [],
            "sources": [],
            "message": "No document id was provided.",
        }

    chunks = list_chunks_by_source(doc_id)
    return {
        "doc_id": doc_id,
        "chunk_count": len(chunks),
        "chunks": chunks,
        "sources": [
            {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "score": 1.0,
                "preview": chunk["preview"],
                "page_number": chunk["page_number"],
                "file_type": chunk["file_type"],
            }
            for chunk in chunks
        ],
    }


def summarize_document(doc_id: str) -> dict:
    if not doc_id:
        return {
            "doc_id": "",
            "summary": "No document id was provided.",
            "sources": [],
        }

    chunks = list_chunks_by_source(doc_id)
    if not chunks:
        return {
            "doc_id": doc_id,
            "summary": f"No document found for '{doc_id}'.",
            "sources": [],
        }

    context = "\n\n".join(
        (
            f"Chunk ID: {chunk['chunk_id']}\n"
            f"Page: {chunk['page_number']}\n"
            f"Content: {chunk['text']}"
        )
        for chunk in chunks
    )
    prompt = (
        "Summarize the following document clearly and concisely.\n"
        "Focus on the main points and key details.\n\n"
        f"Document: {doc_id}\n\n"
        f"{context}\n\n"
        "Summary:"
    )
    summary = generate_response(prompt)

    return {
        "doc_id": doc_id,
        "summary": summary,
        "sources": [
            {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "score": 1.0,
                "preview": chunk["preview"],
                "page_number": chunk["page_number"],
                "file_type": chunk["file_type"],
            }
            for chunk in chunks
        ],
    }


def delete_document(doc_id: str) -> dict:
    if not doc_id:
        return {
            "doc_id": "",
            "deleted_chunks": 0,
            "raw_file_deleted": False,
            "message": "No document id was provided.",
        }

    deleted_chunks = delete_chunks_by_source(doc_id)

    raw_file_deleted = False
    raw_file_path = settings.raw_data_dir_obj / Path(doc_id).name
    if raw_file_path.exists() and raw_file_path.is_file():
        raw_file_path.unlink()
        raw_file_deleted = True

    return {
        "doc_id": doc_id,
        "deleted_chunks": deleted_chunks,
        "raw_file_deleted": raw_file_deleted,
    }
