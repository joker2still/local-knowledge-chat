from fastapi import APIRouter

from backend.app.services.conversation_memory import clear_session, clear_session_messages, list_sessions


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
def get_conversations() -> dict[str, list[str]]:
    return {
        "sessions": list_sessions(),
    }


@router.delete("/{session_id}")
def delete_conversation(session_id: str) -> dict[str, str]:
    clear_session(session_id)
    return {
        "session_id": session_id,
        "status": "deleted",
    }


@router.post("/{session_id}/clear")
def clear_conversation(session_id: str) -> dict[str, str]:
    clear_session_messages(session_id)
    return {
        "session_id": session_id,
        "status": "cleared",
    }
