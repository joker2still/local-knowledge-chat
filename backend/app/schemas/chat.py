from typing import Any

from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str | None = Field(default=None, min_length=1)
    prompt: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def normalize_message(self) -> "ChatRequest":
        if not self.session_id.strip():
            self.session_id = "default"

        if self.message and self.message.strip():
            self.message = self.message.strip()
            return self

        if self.prompt and self.prompt.strip():
            self.message = self.prompt.strip()
            return self

        raise ValueError("message is required")


class ChatSource(BaseModel):
    source: str
    chunk_id: str
    score: float
    preview: str
    page_number: int | None = None
    file_type: str = ""


class ChatResponse(BaseModel):
    answer: str
    selected_tool: str = ""
    tool_result: dict[str, Any] | list[dict[str, Any]] | list[str] | None = None
    sources: list[ChatSource]
    session_id: str = "default"
