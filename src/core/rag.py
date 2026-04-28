import json
from pathlib import Path

from src.core.ai_client import get_ai_client

_KNOWLEDGE_PATH = Path(__file__).parent / "whirlpool_learning_rag_qa.json"

_knowledge: list[dict] | None = None


def _load_knowledge() -> list[dict]:
    global _knowledge
    if _knowledge is None:
        with open(_KNOWLEDGE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _knowledge = data.get("entries", [])
    return _knowledge


def _find_context(question: str, max_entries: int = 5) -> str:
    """Busca entradas relevantes por palabras clave en la pregunta."""
    entries = _load_knowledge()
    question_lower = question.lower()
    words = set(question_lower.split())

    scored: list[tuple[int, dict]] = []
    for entry in entries:
        searchable = (entry.get("question", "") + " " + " ".join(entry.get("tags", []))).lower()
        score = sum(1 for w in words if w in searchable)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [e for _, e in scored[:max_entries]]

    if not top:
        return ""

    return "\n".join(
        f"P: {e['question']}\nR: {e['answer']}" for e in top
    )


def ask(question: str) -> str:
    context = _find_context(question)

    if context:
        system_prompt = (
            "Eres Romina, la asistente virtual de Whirlpool Learning. "
            "Responde en español de forma amigable y concisa. "
            "Usa el siguiente contexto para responder. "
            "Si la respuesta no está en el contexto, dilo honestamente.\n\n"
            f"Contexto:\n{context}"
        )
    else:
        system_prompt = (
            "Eres Romina, la asistente virtual de Whirlpool Learning. "
            "Responde en español de forma amigable y concisa. "
            "No tienes información específica sobre esa pregunta, indícalo y ofrece ayuda general."
        )

    client = get_ai_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        max_tokens=512,
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
