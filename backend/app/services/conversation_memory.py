MAX_MESSAGES_PER_SESSION = 10

_MEMORY: dict[str, list[dict[str, str]]] = {}


def get_recent_messages(session_id: str) -> list[dict[str, str]]:
    return list(_MEMORY.get(session_id, []))


def add_message(session_id: str, role: str, content: str) -> None:
    session_key = session_id.strip() or "default"
    messages = _MEMORY.setdefault(session_key, [])
    messages.append(
        {
            "role": role,
            "content": content,
        }
    )
    _MEMORY[session_key] = messages[-MAX_MESSAGES_PER_SESSION:]


def format_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No prior conversation."

    return "\n".join(
        f"{message.get('role', 'unknown')}: {message.get('content', '')}"
        for message in messages
    )
