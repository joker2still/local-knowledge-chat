from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class ChatSource(BaseModel):
    source: str
    chunk_id: str
    score: float
    preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
