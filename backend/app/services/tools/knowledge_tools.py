from backend.app.services.llm_service import generate_response
from backend.app.services.rag_service import build_rag_prompt, format_sources, retrieve_matches


def search_knowledge_base(query: str) -> dict:
    matches = retrieve_matches(query)
    sources = format_sources(matches)
    return {
        "query": query,
        "result_count": len(sources),
        "sources": [source.model_dump() for source in sources],
        "context": build_rag_prompt(query, matches) if matches else "",
    }


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
