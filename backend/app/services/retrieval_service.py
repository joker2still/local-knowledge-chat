import math

from backend.app.services.document_service import load_chunks
from backend.app.services.embedding_service import generate_embedding


def retrieve_relevant_chunks(question: str, limit: int = 3) -> list[dict]:
    chunks = load_chunks()
    if not chunks:
        return []

    query_embedding = generate_embedding(question)
    scored_chunks = []

    for chunk in chunks:
        embedding = chunk.get("embedding", [])
        if not embedding:
            continue

        similarity = cosine_similarity(query_embedding, embedding)
        scored_chunks.append({**chunk, "similarity": similarity})

    scored_chunks.sort(key=lambda item: item["similarity"], reverse=True)
    return scored_chunks[:limit]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left or not right:
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)
