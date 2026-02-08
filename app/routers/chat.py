from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import asyncio
import base64
import json
import logging
from app.core import config
from app.core.database import save_message, get_history
from app.core.prompts import get_system_prompt
from app.core.dependencies import get_garmin, get_strava, get_code_executor
from app.core.config import get_credential, settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Code execution tag processor
async def process_code_execution_tags(text: str) -> str:
    """Process [EXEC_CODE:language]code[/EXEC_CODE] tags in AI response"""
    import re
    
    code_executor = get_code_executor()
    if not code_executor:
        return text
    
    pattern = r'\[EXEC_CODE:(\w+)\](.*?)\[/EXEC_CODE\]'
    
    def replace_code_tag(match):
        language = match.group(1)
        code = match.group(2).strip()
        
        try:
            if language == "python":
                result = code_executor.run_code(code, "python")
            elif language in ["bash", "shell", "sh"]:
                result = code_executor.run_command(code)
            else:
                return f"\n**[Fel: Språk '{language}' stöds ej]**\n"
            
            output = result.get('output', '')
            error = result.get('error', '')
            
            if error:
                return f"\n**Kodkörning (Docker):**\n```{language}\n{code}\n```\n**Fel:**\n```\n{error}\n```\n"
            else:
                return f"\n**Kodkörning (Docker):**\n```{language}\n{code}\n```\n**Resultat:**\n```\n{output}\n```\n"
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return f"\n**[Fel vid kodkörning: {str(e)}]**\n"
    
    # Replace all code execution tags
    processed = re.sub(pattern, replace_code_tag, text, flags=re.DOTALL)
    return processed

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    session_id: str = "default"
    image: Optional[str] = None # Base64 image data

@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Handles history, context injection (Garmin/Strava), code execution, and LLM generation.
    """
    session_id = request.session_id
    model_id = request.model
    messages = request.messages
    image_data = request.image

    logger.info(f"Chat request [{model_id}]: {len(messages)} messages")
    
    # Extract latest user message
    if messages and messages[-1].role == 'user':
        user_msg = messages[-1].content
    else:
        user_msg = "..." # Should not happen

    # Prepare conversation history for Gemini
    gemini_history = []
    system_prompt = get_system_prompt()
    
    # --- Context Injection ---
    context_parts = []
    
    # Garmin Context
    garmin_tool = get_garmin()
    if garmin_tool and hasattr(garmin_tool, 'cached_data') and garmin_tool.cached_data:
         context_parts.append(f"GARMIN DATA:\n{json.dumps(garmin_tool.cached_data, indent=2, ensure_ascii=False)}")
    
    # Strava Context
    strava_tool = get_strava()
    if strava_tool and hasattr(strava_tool, 'cached_data') and strava_tool.cached_data:
        context_parts.append(f"STRAVA DATA:\n{json.dumps(strava_tool.cached_data, indent=2, ensure_ascii=False)}")

    # Add context to system prompt
    if context_parts:
        context = "\n\n".join(context_parts)
        gemini_history.append({"role": "user", "parts": [f"{system_prompt}\n\nREALTIDSDATA (Kontext):\n{context}"]})
        gemini_history.append({"role": "model", "parts": ["Jag har tagit emot informationen och är redo att hjälpa dig."]})
    else:
        gemini_history.append({"role": "user", "parts": [system_prompt]})
        gemini_history.append({"role": "model", "parts": ["Okej, jag förstår. Hur kan jag hjälpa dig?"]})
    
    # Add conversation history
    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        
        # Handle Image
        if role == "user" and image_data and msg == messages[-1]:
             # Only attach image to the LAST message
             try:
                 if "," in image_data:
                     b64_data = image_data.split(",")[1]
                 else:
                     b64_data = image_data
                 
                 img_bytes = base64.b64decode(b64_data)
                 # Gemini legacy SDK format (google.generativeai)
                 gemini_history.append({
                     "role": role,
                     "parts": [
                         msg.content,
                         {"mime_type": "image/jpeg", "data": img_bytes}
                     ]
                 })
                 logger.info("Image attached to request")
             except Exception as e:
                 logger.error(f"Image decode error: {e}")
                 gemini_history.append({"role": role, "parts": [msg.content]})
        else:
             gemini_history.append({"role": role, "parts": [msg.content]})
    
    # Call Gemini API
    try:
        GOOGLE_API_KEY = get_credential("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
             return {"response": "Error: GOOGLE_API_KEY saknas."}

        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Run async if possible, otherwise executor
        loop = asyncio.get_event_loop()
        gmodel = genai.GenerativeModel(model_id)
        
        # Safety Config using types
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        final_response = await loop.run_in_executor(
            None, 
            lambda: gmodel.generate_content(gemini_history, safety_settings=safety_settings)
        )
        
        response_text = ""
        
        if final_response.candidates:
            candidate = final_response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # Check if we have text content
            if candidate.content and candidate.content.parts:
                response_text = final_response.text
                response_text = await process_code_execution_tags(response_text)
            else:
                # Handle specific finish reasons
                if str(finish_reason) == "12" or finish_reason == 12:
                     response_text = "⚠️ **Säkerhetsfilter triggades (Finish Reason: 12).**\nJag försöker kringgå detta genom att omformulera svaret..."
                     # Fallback strategy could go here, but for now just inform user.
                else:
                     response_text = f"AI genererade inget svar. (Finish Reason: {finish_reason})"
        else:
            response_text = "AI returnerade inget svar."
        
        # Save to DB
        save_message(session_id, "user", user_msg)
        save_message(session_id, "assistant", response_text)
        
        return {"response": response_text}
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {"response": f"Error: {str(e)}"}
