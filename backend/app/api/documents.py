from fastapi import APIRouter, File, UploadFile

from backend.app.schemas.documents import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    ClearDocumentsResponse,
    DeleteDocumentResponse,
    DocumentChunksResponse,
    DocumentListResponse,
    DocumentSummaryResponse,
    UploadResponse,
)
from backend.app.services.document_service import clear_documents, delete_document, delete_documents, ingest_text_file, list_documents
from backend.app.services.tools.document_tools import get_document_chunks, summarize_document


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    return ingest_text_file(file)


@router.get("/documents", response_model=DocumentListResponse)
def get_documents() -> DocumentListResponse:
    return list_documents()


@router.delete("/documents/{filename}", response_model=DeleteDocumentResponse)
def remove_document(filename: str) -> DeleteDocumentResponse:
    return delete_document(filename)


@router.get("/documents/{doc_id}/chunks", response_model=DocumentChunksResponse)
def get_document_chunk_list(doc_id: str) -> DocumentChunksResponse:
    return get_document_chunks(doc_id)


@router.post("/documents/{doc_id}/summary", response_model=DocumentSummaryResponse)
def summarize_document_by_id(doc_id: str) -> DocumentSummaryResponse:
    return summarize_document(doc_id)


@router.post("/documents/delete", response_model=BatchDeleteResponse)
def remove_documents(payload: BatchDeleteRequest) -> BatchDeleteResponse:
    return delete_documents(payload.filenames)


@router.delete("/documents", response_model=ClearDocumentsResponse)
def remove_all_documents() -> ClearDocumentsResponse:
    return clear_documents()
