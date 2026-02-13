from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import logging

# We import the new service instance
from app.services.chat_service import shared_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    session_id: str = "default"
    image: Optional[str] = None  # Base64 image data

@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint. 
    Delegates all logic to UnifiedChatService for consistency with Telegram/Voice.
    """
    session_id = request.session_id
    model_id = request.model
    messages = request.messages
    image_data = request.image

    logger.info(f"Chat request [{model_id}]: {len(messages)} messages")

    if messages and messages[-1].role == "user":
        user_msg = messages[-1].content
    else:
        user_msg = "..."

    # Delegate to Service
    try:
        response_text = await shared_chat_service.process_message(
            session_id=session_id,
            user_msg=user_msg,
            image_data=image_data,
            model_id=model_id,
            # We don't pass full history here because the service loads it from DB.
            # However, for the very first message or if DB is empty, it might be tricky.
            # But since we save every message, DB should be the source of truth.
        )
        return {"response": response_text}

    except Exception as exc:
        logger.error(f"Chat error: {exc}", exc_info=True)
        return {"response": f"Error: {str(exc)}"}
