import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    qdrant_path: str = os.getenv("QDRANT_PATH", "backend/data/qdrant")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "knowledge_base")
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))
    raw_data_dir: str = os.getenv("RAW_DATA_DIR", "backend/data/raw")
    upload_chunk_size: int = int(os.getenv("UPLOAD_CHUNK_SIZE", "500"))
    upload_chunk_overlap: int = int(os.getenv("UPLOAD_CHUNK_OVERLAP", "100"))

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


settings = Settings()
