from backend.app.services.embedding_service import generate_embedding
from backend.app.services.llm_service import generate_response
from backend.app.services.vector_store import search_chunks


SYSTEM_INSTRUCTION = (
    "You are a helpful assistant for local knowledge chat. "
    "Answer only from the provided context. "
    "If the context is insufficient, say you do not know."
)


def answer_question(question: str) -> dict:
    query_embedding = generate_embedding(question)
    matches = search_chunks(query_embedding, limit=3)

    if not matches:
        return {
            "answer": "No documents are available yet. Please upload a .txt file first.",
            "sources": [],
        }

    prompt = build_rag_prompt(question, matches)
    answer = generate_response(prompt)

    sources = []
    for match in matches:
        payload = match["payload"]
        text = str(payload.get("text", ""))
        sources.append(
            {
                "filename": payload.get("source", ""),
                "chunk_id": payload.get("chunk_id", match["id"]),
                "text_preview": text[:120],
                "similarity": round(match["score"], 4),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
    }


def build_rag_prompt(question: str, matches: list[dict]) -> str:
    context = "\n\n".join(
        (
            f"Source: {item['payload'].get('source', '')}#"
            f"{item['payload'].get('chunk_id', item['id'])}\n"
            f"Content: {item['payload'].get('text', '')}"
        )
        for item in matches
    )
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Context:\n{context}\n\n"
        f"User question: {question}\n"
        "Answer:"
    )
