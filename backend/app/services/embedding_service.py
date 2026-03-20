import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL_NAME = "nomic-embed-text"

def generate_embedding(text: str) -> list[float]:
    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBEDDING_MODEL_NAME,
                "prompt": text,
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to call local Ollama embeddings API: {exc}") from exc

    data = response.json()
    embedding = data.get("embedding")
    if not embedding:
        raise RuntimeError(f"Ollama embeddings API returned no embedding: {data}")

    return embedding