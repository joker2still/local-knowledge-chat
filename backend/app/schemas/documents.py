from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    filename: str
    chunks: int
    vector_store: str


class DocumentItem(BaseModel):
    filename: str
    file_type: str = ""
    chunks: int
    page_count: int = 0


class DocumentListResponse(BaseModel):
    documents: list[DocumentItem]
    total_files: int
    total_chunks: int


class DocumentChunkItem(BaseModel):
    chunk_id: str
    source: str
    page_number: int | None = None
    file_type: str = ""
    text: str
    preview: str


class DocumentChunksResponse(BaseModel):
    doc_id: str
    chunk_count: int
    chunks: list[DocumentChunkItem]


class DocumentSummaryResponse(BaseModel):
    doc_id: str
    summary: str
    sources: list[dict]


class DeleteDocumentResponse(BaseModel):
    filename: str
    deleted_chunks: int
    raw_file_deleted: bool


class BatchDeleteRequest(BaseModel):
    filenames: list[str] = Field(..., min_length=1)


class BatchDeleteItem(BaseModel):
    filename: str
    deleted_chunks: int
    raw_file_deleted: bool
    found: bool


class BatchDeleteResponse(BaseModel):
    results: list[BatchDeleteItem]
    deleted_files: int
    deleted_chunks: int


class ClearDocumentsResponse(BaseModel):
    deleted_files: int
    deleted_chunks: int
    raw_files_deleted: int
