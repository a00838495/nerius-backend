from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.rag import ask

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    if not body.message.strip():
        raise HTTPException(status_code=422, detail="El mensaje no puede estar vacío")
    reply = ask(body.message)
    return ChatResponse(reply=reply)
