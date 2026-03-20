from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.services.document_service import ingest_text_file


router = APIRouter()


@router.post("/upload")
def upload_document(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    try:
        result = ingest_text_file(file)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result
