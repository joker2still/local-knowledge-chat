from fastapi import APIRouter, File, UploadFile

from backend.app.schemas.documents import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    ClearDocumentsResponse,
    DeleteDocumentResponse,
    DocumentListResponse,
    UploadResponse,
)
from backend.app.services.document_service import clear_documents, delete_document, delete_documents, ingest_text_file, list_documents


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


@router.post("/documents/delete", response_model=BatchDeleteResponse)
def remove_documents(payload: BatchDeleteRequest) -> BatchDeleteResponse:
    return delete_documents(payload.filenames)


@router.delete("/documents", response_model=ClearDocumentsResponse)
def remove_all_documents() -> ClearDocumentsResponse:
    return clear_documents()
