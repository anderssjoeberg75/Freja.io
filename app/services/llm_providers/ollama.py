import httpx
import logging
from typing import List, Dict, Optional, Any
from app.core.config import get_credential, settings

logger = logging.getLogger(__name__)

async def generate_ollama_response(
    model_id: str,
    system_prompt: str,
    history: List[Dict[str, Any]],
    user_msg: str,
    image_data: Optional[str] = None
) -> str:
    """
    Generates response using Ollama API.
    Does not support tools yet.
    """
    ollama_url = get_credential("OLLAMA_URL") or settings.OLLAMA_URL
    base_url = ollama_url.rstrip("/")
    
    # Convert Gemini-style history to Ollama format
    messages = []
    
    # System prompt
    messages.append({"role": "system", "content": system_prompt})
    
    # History
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        # Extract text parts
        content = ""
        for part in msg.get("parts", []):
            if isinstance(part, str):
                content += part
            elif hasattr(part, "text"):
                content += part.text
            elif isinstance(part, dict) and "text" in part:
                 content += part["text"]
        
        if content:
            messages.append({"role": role, "content": content})
            
    # Current message
    current_msg = {"role": "user", "content": user_msg}
    if image_data:
         if "," in image_data:
             b64 = image_data.split(",", 1)[1]
         else:
             b64 = image_data
         current_msg["images"] = [b64]
         
    messages.append(current_msg)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": model_id,
                "messages": messages,
                "stream": False
            }
            logger.info(f"Sending request to Ollama ({model_id})...")
            resp = await client.post(f"{base_url}/api/chat", json=payload)
            
            if resp.status_code != 200:
                return f"Ollama Error: {resp.status_code} - {resp.text}"
                
            data = resp.json()
            return str(data.get("message", {}).get("content", "Error: Empty response from Ollama"))
    except Exception as e:
        logger.error(f"Ollama generation error: {e}")
        return f"Error connecting to Ollama: {str(e)}"
