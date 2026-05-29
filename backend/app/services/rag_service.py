import logging

from backend.app.core.config import settings
from backend.app.schemas.chat import ChatResponse, ChatSource
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.llm_service import generate_response
from backend.app.services.query_rewrite_service import rewrite_query
from backend.app.services.vector_store import count_chunks, search_chunks


logger = logging.getLogger(__name__)

INSUFFICIENT_CONTEXT_MESSAGE = "\u6211\u6ca1\u6709\u5728\u5f53\u524d\u77e5\u8bc6\u5e93\u4e2d\u627e\u5230\u8db3\u591f\u53ef\u9760\u7684\u4f9d\u636e\u3002"

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant for local knowledge chat. "
    "Answer only from the provided context. "
    "If the context is insufficient, reply with exactly: "
    f"{INSUFFICIENT_CONTEXT_MESSAGE}"
)


def retrieve_matches(query: str, limit: int | None = None, min_score: float | None = None) -> list[dict]:
    query_embedding = generate_embedding(query)
    raw_matches = search_chunks(query_embedding, limit=limit or settings.retrieval_top_k)
    threshold = settings.retrieval_score_threshold if min_score is None else min_score
    filtered_matches = [match for match in raw_matches if float(match.get("score", 0.0)) >= threshold]
    logger.info(
        "chat_retrieval_done top_k=%s raw_result_count=%s filtered_result_count=%s threshold=%s",
        limit or settings.retrieval_top_k,
        len(raw_matches),
        len(filtered_matches),
        threshold,
    )
    return filtered_matches


def format_sources(matches: list[dict]) -> list[ChatSource]:
    sources = []
    for match in matches:
        payload = match.get("payload", {})
        text = str(payload.get("text", ""))
        sources.append(
            ChatSource(
                source=str(payload.get("source", "")),
                chunk_id=str(payload.get("chunk_id", match.get("id", ""))),
                score=float(match.get("score", 0.0)),
                preview=text[:200],
                page_number=payload.get("page_number"),
                file_type=str(payload.get("file_type", "")),
            )
        )
    return sources


def build_rag_prompt(question: str, matches: list[dict], rewritten_query: str = "") -> str:
    context = "\n\n".join(
        (
            f"Source: {item.get('payload', {}).get('source', '')}#"
            f"{item.get('payload', {}).get('chunk_id', item.get('id', ''))}\n"
            f"Page: {item.get('payload', {}).get('page_number', '')}\n"
            f"Content: {item.get('payload', {}).get('text', '')}"
        )
        for item in matches
    )

    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Rewritten retrieval query: {rewritten_query or question}\n\n"
        f"Context:\n{context}\n\n"
        f"User question: {question}\n"
        "Answer:"
    )


def search_knowledge_context(question: str, history_text: str = "", limit: int | None = None) -> dict:
    original_question = question.strip()
    rewritten_query = rewrite_query(original_question, history_text) if original_question else ""

    if count_chunks() == 0:
        return {
            "original_question": original_question,
            "rewritten_query": rewritten_query or original_question,
            "result_count": 0,
            "sources": [],
            "context": "",
            "insufficient_context": True,
            "message": INSUFFICIENT_CONTEXT_MESSAGE,
        }

    matches = retrieve_matches(rewritten_query or original_question, limit=limit)
    sources = format_sources(matches)
    if not matches:
        return {
            "original_question": original_question,
            "rewritten_query": rewritten_query or original_question,
            "result_count": 0,
            "sources": [],
            "context": "",
            "insufficient_context": True,
            "message": INSUFFICIENT_CONTEXT_MESSAGE,
        }

    return {
        "original_question": original_question,
        "rewritten_query": rewritten_query or original_question,
        "result_count": len(sources),
        "sources": [source.model_dump() for source in sources],
        "context": build_rag_prompt(original_question, matches, rewritten_query or original_question),
        "insufficient_context": False,
    }


def answer_with_knowledge_base(question: str, history_text: str = "") -> ChatResponse:
    logger.info("chat_request_received question_length=%s", len(question))
    result = search_knowledge_context(question, history_text=history_text)
    sources = [ChatSource(**item) for item in result.get("sources", [])]

    if result.get("insufficient_context"):
        return ChatResponse(
            answer=INSUFFICIENT_CONTEXT_MESSAGE,
            original_question=question,
            rewritten_query=str(result.get("rewritten_query", question)),
            selected_tool="search_knowledge_base",
            tool_result=result,
            sources=sources,
        )

    prompt = str(result.get("context", ""))
    answer = generate_response(prompt)
    return ChatResponse(
        answer=answer,
        original_question=question,
        rewritten_query=str(result.get("rewritten_query", question)),
        selected_tool="search_knowledge_base",
        tool_result=result,
        sources=sources,
    )
