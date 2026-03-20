import requests


OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
CHAT_MODEL_NAME = "qwen2.5"


def generate_response(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json={
                "model": CHAT_MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError("Failed to call local Ollama API") from exc

    data = response.json()
    return data.get("response", "")
