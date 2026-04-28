from groq import Groq

from src.core.config import settings

_client: Groq | None = None


def get_ai_client() -> Groq:
    global _client
    if _client is None:
        if not settings.ai_api_key:
            raise RuntimeError("AI_API_KEY no está configurada en el .env")
        _client = Groq(api_key=settings.ai_api_key)
    return _client
