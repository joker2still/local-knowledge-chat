from backend.app.services.llm_service import generate_response
from backend.app.services.rag_service import search_knowledge_context


def search_knowledge_base(query: str, history_text: str = "") -> dict:
    return search_knowledge_context(query, history_text=history_text)


def answer_directly(question: str) -> dict:
    answer = generate_response(
        "Answer the user question directly and clearly. "
        "Do not mention any missing tool usage.\n\n"
        f"User question: {question}\n"
        "Answer:"
    )
    return {
        "question": question,
        "draft_answer": answer,
    }
