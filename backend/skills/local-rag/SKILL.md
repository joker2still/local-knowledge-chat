---
name: local-rag
description: Work on the Local Knowledge Chat backend RAG pipeline, including document ingestion, chunking, embeddings, Qdrant local search, Ollama prompts, and API verification.
---

# Local RAG Skill

Use this skill when changing or reviewing the backend RAG flow for this repository.

## Scope

This project is a local Retrieval-Augmented Generation app:

- Upload `.txt` or `.pdf` documents through `POST /upload`.
- Extract text, split it into overlapping chunks, and create embeddings with Ollama.
- Store vectors and metadata in local Qdrant.
- Answer `POST /chat` questions by embedding the query, retrieving top chunks, and prompting the chat model with retrieved context.

## Key Files

- `backend/app/main.py`: FastAPI app setup, CORS, exception handlers, router registration.
- `backend/app/api/documents.py`: upload endpoint.
- `backend/app/api/chat.py`: chat endpoint.
- `backend/app/core/config.py`: environment-backed settings.
- `backend/app/core/exceptions.py`: app-specific exception types.
- `backend/app/services/document_service.py`: file validation, raw file persistence, text extraction, chunking, embedding, upsert.
- `backend/app/services/vector_store.py`: Qdrant local collection setup, upsert, search, count.
- `backend/app/services/rag_service.py`: retrieval orchestration, RAG prompt construction, source formatting.
- `backend/app/services/embedding_service.py`: Ollama embedding calls.
- `backend/app/services/llm_service.py`: Ollama generation calls.
- `backend/app/schemas`: request and response models.

## RAG Invariants

- Answers should be grounded in retrieved context.
- If no chunks are available, return a clear upload-first message with no sources.
- Keep source metadata stable for the frontend: `source`, `chunk_id`, `score`, `preview`, `page_number`, `file_type`.
- Preserve PDF page numbers when extracting text.
- Do not silently accept unsupported file types.
- Do not remove overlap chunking unless replacing it with a tested chunking strategy.
- Keep Qdrant vector size aligned with the embedding model output.

## Configuration

Important environment variables:

- `OLLAMA_BASE_URL`, default `http://localhost:11434`
- `OLLAMA_CHAT_MODEL`, default `qwen2.5`
- `OLLAMA_EMBEDDING_MODEL`, default `nomic-embed-text`
- `QDRANT_PATH`, default `backend/data/qdrant`
- `QDRANT_COLLECTION`, default `knowledge_base`
- `RETRIEVAL_TOP_K`, default `3`
- `RAW_DATA_DIR`, default `backend/data/raw`
- `UPLOAD_CHUNK_SIZE`, default `500`
- `UPLOAD_CHUNK_OVERLAP`, default `100`

When adding a new setting, update `backend/.env.example` and provide a conservative default.

## Implementation Guidance

- Keep API handlers thin; place business logic in services.
- Use Pydantic schemas for API contracts.
- Raise `AppError` for expected user-facing failures such as invalid file type, invalid encoding, empty document, or PDF parse errors.
- Wrap external service failures with the existing external-service exception pattern.
- Prefer small focused functions for parsing, chunking, retrieval, and prompt building so they can be tested independently.
- Avoid storing secrets, uploaded documents, or generated vector data in git.

## Verification Checklist

1. Start backend:

```bash
uvicorn backend.app.main:app --reload
```

2. Check health:

```bash
curl http://127.0.0.1:8000/health
```

3. Upload a document:

```bash
curl -X POST "http://127.0.0.1:8000/upload" -F "file=@sample.txt"
```

4. Ask a grounded question:

```bash
curl -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d "{\"prompt\":\"What does the document say?\"}"
```

5. Confirm the response includes an answer and source metadata.
