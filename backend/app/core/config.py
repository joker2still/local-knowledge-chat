import os
from dataclasses import dataclass
from pathlib import Path


def _get_env(name: str, default: str, legacy_name: str | None = None) -> str:
    if name in os.environ:
        return os.environ[name]
    if legacy_name and legacy_name in os.environ:
        return os.environ[legacy_name]
    return default


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = _get_env("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = _get_env("OLLAMA_CHAT_MODEL", "qwen2.5")
    ollama_embedding_model: str = _get_env("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    qdrant_path: str = _get_env("QDRANT_PATH", "backend/data/qdrant")
    qdrant_collection_name: str = _get_env("QDRANT_COLLECTION_NAME", "knowledge_base", legacy_name="QDRANT_COLLECTION")
    retrieval_top_k: int = int(_get_env("RETRIEVAL_TOP_K", "5", legacy_name="TOP_K"))
    retrieval_score_threshold: float = float(_get_env("RETRIEVAL_SCORE_THRESHOLD", "0.35"))
    raw_data_dir: str = _get_env("RAW_DATA_DIR", "backend/data/raw")
    upload_chunk_size: int = int(_get_env("UPLOAD_CHUNK_SIZE", "500"))
    upload_chunk_overlap: int = int(_get_env("UPLOAD_CHUNK_OVERLAP", "100"))

    @property
    def ollama_generate_url(self) -> str:
        return f"{self.ollama_base_url.rstrip('/')}/api/generate"

    @property
    def ollama_embeddings_url(self) -> str:
        return f"{self.ollama_base_url.rstrip('/')}/api/embeddings"

    @property
    def qdrant_path_obj(self) -> Path:
        return Path(self.qdrant_path)

    @property
    def raw_data_dir_obj(self) -> Path:
        return Path(self.raw_data_dir)

    @property
    def qdrant_collection(self) -> str:
        return self.qdrant_collection_name


settings = Settings()
