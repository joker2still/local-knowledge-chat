from fastapi import APIRouter, File, UploadFile

from backend.app.schemas.documents import UploadResponse
from backend.app.services.document_service import ingest_text_file


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    return ingest_text_file(file)
