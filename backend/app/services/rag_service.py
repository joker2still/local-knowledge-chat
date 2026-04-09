import logging

from backend.app.core.config import settings
from backend.app.schemas.chat import ChatResponse, ChatSource
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.llm_service import generate_response
from backend.app.services.vector_store import search_chunks


logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant for local knowledge chat. "
    "Answer only from the provided context. "
    "If the context is insufficient, say you do not know."
)


def answer_question(question: str) -> ChatResponse:
    logger.info("chat_request_received question_length=%s", len(question))

    query_embedding = generate_embedding(question)
    matches = search_chunks(query_embedding, limit=settings.retrieval_top_k)

    logger.info("chat_retrieval_done top_k=%s result_count=%s", settings.retrieval_top_k, len(matches))

    if not matches:
        return ChatResponse(
            answer="No documents are available yet. Please upload a .txt file first.",
            sources=[],
        )

    prompt = build_rag_prompt(question, matches)
    answer = generate_response(prompt)

    sources = []
    for match in matches:
        payload = match.get("payload", {})
        text = str(payload.get("text", ""))
        sources.append(
            ChatSource(
                source=str(payload.get("source", "")),
                chunk_id=str(payload.get("chunk_id", match.get("id", ""))),
                score=float(match.get("score", 0.0)),
                preview=text[:120],
            )
        )

    return ChatResponse(answer=answer, sources=sources)


def build_rag_prompt(question: str, matches: list[dict]) -> str:
    context = "\n\n".join(
        (
            f"Source: {item.get('payload', {}).get('source', '')}#"
            f"{item.get('payload', {}).get('chunk_id', item.get('id', ''))}\n"
            f"Content: {item.get('payload', {}).get('text', '')}"
        )
        for item in matches
    )

    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Context:\n{context}\n\n"
        f"User question: {question}\n"
        "Answer:"
    )
