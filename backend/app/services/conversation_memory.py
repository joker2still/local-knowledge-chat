import json
import logging
import re
from pathlib import Path


logger = logging.getLogger(__name__)

MAX_MESSAGES_PER_SESSION = 50
CONVERSATIONS_DIR = Path("backend/data/conversations")

_MEMORY: dict[str, list[dict[str, str]]] = {}


def sanitize_session_id(session_id: str) -> str:
    normalized = (session_id or "default").strip() or "default"
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", normalized)
    return sanitized or "default"


def get_session_path(session_id: str) -> Path:
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return CONVERSATIONS_DIR / f"{sanitize_session_id(session_id)}.json"


def load_history(session_id: str) -> list[dict[str, str]]:
    normalized_session_id = sanitize_session_id(session_id)
    if normalized_session_id in _MEMORY:
        return list(_MEMORY[normalized_session_id])

    session_path = get_session_path(normalized_session_id)
    if not session_path.exists():
        _MEMORY[normalized_session_id] = []
        return []

    try:
        payload = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("conversation_history_load_failed session_id=%s", normalized_session_id)
        _MEMORY[normalized_session_id] = []
        return []

    messages = payload.get("messages", [])
    if not isinstance(messages, list):
        logger.warning("conversation_history_invalid_format session_id=%s", normalized_session_id)
        _MEMORY[normalized_session_id] = []
        return []

    normalized_messages = [
        {
            "role": str(message.get("role", "")),
            "content": str(message.get("content", "")),
        }
        for message in messages
        if isinstance(message, dict)
    ][-MAX_MESSAGES_PER_SESSION:]

    _MEMORY[normalized_session_id] = normalized_messages
    return list(normalized_messages)


def save_history(session_id: str, messages: list[dict[str, str]]) -> None:
    normalized_session_id = sanitize_session_id(session_id)
    normalized_messages = [
        {
            "role": str(message.get("role", "")),
            "content": str(message.get("content", "")),
        }
        for message in messages
    ][-MAX_MESSAGES_PER_SESSION:]

    _MEMORY[normalized_session_id] = normalized_messages
    session_path = get_session_path(normalized_session_id)
    payload = {
        "session_id": normalized_session_id,
        "messages": normalized_messages,
    }
    session_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_message(session_id: str, role: str, content: str) -> None:
    normalized_session_id = sanitize_session_id(session_id)
    messages = load_history(normalized_session_id)
    messages.append(
        {
            "role": role,
            "content": content,
        }
    )
    save_history(normalized_session_id, messages)


def clear_session(session_id: str) -> None:
    normalized_session_id = sanitize_session_id(session_id)
    _MEMORY.pop(normalized_session_id, None)
    session_path = get_session_path(normalized_session_id)
    if session_path.exists():
        session_path.unlink()


def clear_session_messages(session_id: str) -> None:
    normalized_session_id = sanitize_session_id(session_id)
    save_history(normalized_session_id, [])


def list_sessions() -> list[str]:
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(file.stem for file in CONVERSATIONS_DIR.glob("*.json"))


def get_recent_messages(session_id: str) -> list[dict[str, str]]:
    return load_history(session_id)


def add_message(session_id: str, role: str, content: str) -> None:
    append_message(session_id, role, content)


def format_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No prior conversation."

    return "\n".join(
        f"{message.get('role', 'unknown')}: {message.get('content', '')}"
        for message in messages
    )
