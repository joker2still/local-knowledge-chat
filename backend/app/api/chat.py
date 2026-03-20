from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.rag_service import answer_question


router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


@router.post("/chat")
def chat(payload: ChatRequest) -> dict:
    try:
        return answer_question(payload.prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
