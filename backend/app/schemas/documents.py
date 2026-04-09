from pydantic import BaseModel


class UploadResponse(BaseModel):
    filename: str
    chunks: int
    vector_store: str
