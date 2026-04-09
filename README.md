# Local Knowledge Chat

## 1. Project Overview
Local Knowledge Chat is a minimal local RAG (Retrieval-Augmented Generation) application.
It lets you upload `.txt` documents, stores embeddings in local Qdrant, and answers questions with context retrieved from your uploaded files.

## 2. Features
- FastAPI backend with clean service-based structure
- React + TypeScript frontend (Vite)
- `.txt` document upload and chunking
- Local embedding generation via Ollama
- Local vector search via Qdrant (embedded/local mode)
- RAG chat answers with source snippets
- CORS enabled for frontend dev server

## 3. Tech Stack
- Backend: FastAPI, Pydantic, Requests
- Vector store: Qdrant (`qdrant-client`, local mode)
- LLM/Embeddings: Ollama
- Frontend: React + TypeScript + Vite

## 4. Project Structure
```text
local-knowledge-chat/
  backend/
    app/
      main.py
      api/
        chat.py
        documents.py
      core/
        config.py
        logging_config.py
        exceptions.py
      schemas/
        chat.py
        documents.py
      services/
        llm_service.py
        embedding_service.py
        document_service.py
        vector_store.py
        rag_service.py
    data/
      raw/
      qdrant/
    .env.example
    requirements.txt
  frontend/
    src/
      App.tsx
      services/
        api.ts
      types.ts
    package.json
```

## 5. Backend Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```
3. (Optional) create `.env` from `.env.example` and adjust values.
4. Start backend:
```bash
uvicorn backend.app.main:app --reload
```
Backend default URL: `http://127.0.0.1:8000`

## 6. Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```
2. Start dev server:
```bash
npm run dev
```
Frontend default URL: `http://127.0.0.1:5173`

## 7. How to Run Ollama
1. Start Ollama service:
```bash
ollama serve
```
2. Pull required models:
```bash
ollama pull qwen2.5
ollama pull nomic-embed-text
```
3. Confirm Ollama is reachable:
- Base URL: `http://localhost:11434`

## 8. How to Test Upload and Chat
1. Start Ollama, backend, and frontend.
2. Upload a `.txt` file from frontend upload section.
3. Ask a question in chat input.
4. Verify answer and sources are shown.

You can also test APIs directly with curl (see below).

## 9. Example API Usage
### Health
```bash
curl http://127.0.0.1:8000/health
```

### Upload
```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@sample.txt"
```

### Chat
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"What does the document say about FastAPI?\"}"
```

Example chat response:
```json
{
  "answer": "...",
  "sources": [
    {
      "source": "sample.txt",
      "chunk_id": "...",
      "score": 0.72,
      "preview": "..."
    }
  ]
}
```

## 10. Future Improvements
- Add automated tests for services and API routes
- Add file type validation beyond extension check
- Support PDF/Markdown ingestion
- Add metadata filters and hybrid search
- Add Docker Compose for one-command local startup
- Add conversation history and multi-turn context
