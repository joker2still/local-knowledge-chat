from backend.app.services.llm_service import generate_response
from backend.app.services.retrieval_service import retrieve_relevant_chunks


SYSTEM_INSTRUCTION = (
    "You are a helpful assistant for local knowledge chat. "
    "Answer only from the provided context. "
    "If the context is insufficient, say you do not know."
)


def answer_question(question: str) -> dict:
    chunks = retrieve_relevant_chunks(question, limit=3)
    if not chunks:
        return {
            "answer": "No documents are available yet. Please upload a .txt file first.",
            "sources": [],
        }

    prompt = build_rag_prompt(question, chunks)
    answer = generate_response(prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "filename": chunk["filename"],
                "chunk_id": chunk["id"],
                "text_preview": chunk["text"][:120],
                "similarity": round(chunk["similarity"], 4),
            }
            for chunk in chunks
        ],
    }


def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"Source: {chunk['filename']}#{chunk['id']}\nContent: {chunk['text']}"
        for chunk in chunks
    )
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Context:\n{context}\n\n"
        f"User question: {question}\n"
        "Answer:"
    )
