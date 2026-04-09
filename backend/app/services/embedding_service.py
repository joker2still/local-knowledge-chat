import logging

import requests

from backend.app.core.config import settings
from backend.app.core.exceptions import ExternalServiceError


logger = logging.getLogger(__name__)


def generate_embedding(text: str) -> list[float]:
    try:
        response = requests.post(
            settings.ollama_embeddings_url,
            json={
                "model": settings.ollama_embedding_model,
                "prompt": text,
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Ollama embedding call failed")
        raise ExternalServiceError("Failed to call Ollama embeddings API") from exc

    data = response.json()
    embedding = data.get("embedding")
    if not embedding:
        raise ExternalServiceError("Ollama embeddings API returned no embedding")

    return embedding
