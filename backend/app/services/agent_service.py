import json
import logging
import re

from backend.app.schemas.chat import ChatResponse
from backend.app.services.llm_service import generate_response
from backend.app.services.tools.document_tools import delete_document, get_document_chunks, list_documents, summarize_document
from backend.app.services.tools.knowledge_tools import answer_directly, search_knowledge_base


logger = logging.getLogger(__name__)

AVAILABLE_TOOLS = {
    "search_knowledge_base": search_knowledge_base,
    "answer_directly": answer_directly,
    "list_documents": list_documents,
    "get_document_chunks": get_document_chunks,
    "summarize_document": summarize_document,
    "delete_document": delete_document,
}

TOOL_DECISION_PROMPT = """You are a routing agent for a local knowledge chat system.
Choose exactly one tool for the user request.

Available tools:
- search_knowledge_base: use for questions likely answered by uploaded documents
- answer_directly: use for general questions that do not need the knowledge base
- list_documents: use when the user asks what documents are available
- get_document_chunks: use when the user asks to show contents or chunks of a specific document
- summarize_document: use when the user asks to summarize a specific document
- delete_document: use when the user asks to delete or remove a specific document

Return strict JSON only with this schema:
{{"tool":"search_knowledge_base|answer_directly|list_documents|get_document_chunks|summarize_document|delete_document","reason":"short reason","query":"rewritten query if needed","doc_id":"optional document id or file name"}}

Rules:
- Always return valid JSON
- Use search_knowledge_base when the user asks about uploaded documents, files, knowledge base content, summaries, or specific information.
- Use list_documents when the user asks what documents are uploaded.
- If user asks to summarize a specific document, use summarize_document.
- If user asks to show contents/chunks of a document, use get_document_chunks.
- If user asks to delete/remove a document, use delete_document.
- Use answer_directly for greetings, general questions, or questions unrelated to the knowledge base.
- For list_documents, set query to ""
- For get_document_chunks, summarize_document, and delete_document, set doc_id to the file name when possible.
- Keep reason short
- Do not include markdown or explanation
- Do not include markdown in the JSON

User question:
{question}
"""


def answer_question(question: str) -> ChatResponse:
    logger.info("agent_request_received question_length=%s", len(question))

    decision = decide_tool(question)
    selected_tool = str(decision.get("tool", "search_knowledge_base"))
    tool_query = str(decision.get("query", question))
    tool_doc_id = str(decision.get("doc_id", "")).strip()

    tool_result = execute_tool(selected_tool, question, tool_query, tool_doc_id)
    selected_tool = str(tool_result.get("selected_tool", selected_tool))
    final_answer = generate_final_answer(question, selected_tool, tool_result)
    sources = tool_result.get("sources", []) if isinstance(tool_result, dict) else []

    return ChatResponse(
        answer=final_answer,
        selected_tool=selected_tool,
        tool_result=tool_result,
        sources=sources,
    )


def decide_tool(question: str) -> dict:
    raw_decision = generate_response(TOOL_DECISION_PROMPT.format(question=question))
    parsed_decision = parse_tool_decision(raw_decision)
    if not parsed_decision:
        logger.warning("agent_tool_decision_parse_failed fallback=search_knowledge_base")
        return {"tool": "search_knowledge_base", "reason": "fallback after parse failure", "query": question}

    tool_name = str(parsed_decision.get("tool", "")).strip()
    if tool_name not in AVAILABLE_TOOLS:
        logger.warning("agent_tool_invalid tool=%s fallback=search_knowledge_base", tool_name)
        return {"tool": "search_knowledge_base", "reason": "fallback after invalid tool", "query": question}

    if tool_name == "list_documents":
        return {
            "tool": tool_name,
            "reason": str(parsed_decision.get("reason", "")).strip(),
            "query": "",
            "doc_id": "",
        }

    return {
        "tool": tool_name,
        "reason": str(parsed_decision.get("reason", "")).strip(),
        "query": str(parsed_decision.get("query", question)).strip() or question,
        "doc_id": str(parsed_decision.get("doc_id", "")).strip(),
    }


def parse_tool_decision(raw_decision: str) -> dict | None:
    try:
        return json.loads(raw_decision)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_decision, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def execute_tool(selected_tool: str, question: str, tool_input: str, doc_id: str) -> dict:
    if selected_tool == "list_documents":
        result = list_documents()
    elif selected_tool == "get_document_chunks":
        result = get_document_chunks(doc_id)
    elif selected_tool == "summarize_document":
        result = summarize_document(doc_id)
    elif selected_tool == "delete_document":
        result = delete_document(doc_id)
    elif selected_tool == "answer_directly":
        result = answer_directly(tool_input or question)
    else:
        selected_tool = "search_knowledge_base"
        result = search_knowledge_base(tool_input or question)

    logger.info("agent_tool_executed tool=%s", selected_tool)
    result["selected_tool"] = selected_tool
    return result


def generate_final_answer(question: str, selected_tool: str, tool_result: dict) -> str:
    prompt = (
        "You are a helpful assistant for a local knowledge chat system.\n"
        "Use the selected tool result to answer the user.\n"
        "If the tool result contains sources or context, rely on them.\n"
        "If the tool is list_documents, summarize the available documents clearly.\n"
        "If the tool is answer_directly, improve or restate the draft answer if useful.\n"
        "Do not mention internal routing unless the user asked.\n\n"
        f"User question: {question}\n"
        f"Selected tool: {selected_tool}\n"
        f"Tool result:\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}\n\n"
        "Final answer:"
    )
    return generate_response(prompt)
