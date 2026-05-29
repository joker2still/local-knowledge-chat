import logging

from backend.app.services.llm_service import generate_response


logger = logging.getLogger(__name__)

QUERY_REWRITE_PROMPT = """You rewrite user questions for vector search in a local knowledge base.
Given the recent conversation and the current user question, produce one concise search query.

Rules:
- Resolve references like "it", "that file", "the previous document" when possible.
- Keep the query explicit and short.
- Preserve important names, file names, dates, and domain terms.
- Return plain text only.
- Do not add explanation, markdown, quotes, or JSON.

Recent conversation:
{history}

Current user question:
{question}

Search query:
"""


def rewrite_query(question: str, history_text: str) -> str:
    if not question.strip():
        return ""

    try:
        rewritten = generate_response(
            QUERY_REWRITE_PROMPT.format(
                history=history_text or "No prior conversation.",
                question=question.strip(),
            )
        ).strip()
    except Exception:
        logger.warning("query_rewrite_failed fallback=original_question")
        return question.strip()

    if not rewritten:
        return question.strip()

    normalized = " ".join(rewritten.split())
    logger.info("query_rewritten original_length=%s rewritten_length=%s", len(question), len(normalized))
    return normalized or question.strip()
