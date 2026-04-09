import logging

import requests

from backend.app.core.config import settings
from backend.app.core.exceptions import ExternalServiceError


logger = logging.getLogger(__name__)


def generate_response(prompt: str) -> str:
    try:
        response = requests.post(
            settings.ollama_generate_url,
            json={
                "model": settings.ollama_chat_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Ollama generate call failed")
        raise ExternalServiceError("Failed to call Ollama generate API") from exc

    data = response.json()
    return str(data.get("response", ""))
