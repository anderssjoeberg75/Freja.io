from fastapi import APIRouter
from pydantic import BaseModel
import google.generativeai as genai
import requests
import json
import time
import asyncio
import logging
from typing import List, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Importera databasfunktioner
from app.core.database import save_message, get_history
# Importera System Prompt
from app.core.prompts import get_system_prompt
# Importera Settings
from app.core.config import settings, get_credential
# Importera Tools
from app.tools.garmin_core import GarminCoach
from app.tools.strava_core import StravaTool

# Importera DB-funktioner
from app.core.database import get_db_settings, save_db_setting, get_db_prompts, save_db_prompt

router = APIRouter()

# Kontrollera om Gemini SDK finns
try:
    import google.generativeai as genai
    has_google = True
except ImportError:
    has_google = False

# --- LAZY INIT TOOLS ---
garmin_tool = None
strava_tool = None
GLOBAL_CODE_EXECUTOR = None

# Garmin cache
cached_garmin_data = None
last_garmin_fetch = 0

# Strava cache
cached_strava_data = None
last_strava_fetch = 0

# Code Executor import
try:
    from app.tools.code_executor import CodeExecutor
    has_docker = True
except ImportError:
    has_docker = False

# Cache for /api/models (TTL: 5 minutes)
_model_cache = {"data": [], "timestamp": 0}
CACHE_TTL = 300  # 5 minutes

def init_tools():
    """Initialize tools lazily on first request"""
    global garmin_tool, strava_tool, GLOBAL_CODE_EXECUTOR
    
    # Garmin - Use credential helper
    GARMIN_EMAIL = get_credential("GARMIN_EMAIL")
    GARMIN_PASSWORD = get_credential("GARMIN_PASSWORD")
    
    if GARMIN_EMAIL and GARMIN_PASSWORD:
        try:
            if not garmin_tool:  # Only init if not already done
                garmin_tool = GarminCoach()
                logger.info("Garmin tool initialized successfully")
        except Exception as e:
            logger.error(f"Garmin init failed: {e}")
    else:
        logger.info("Garmin skipped (missing credentials)")

    # Strava - Use credential helper (ALWAYS reinit to get fresh credentials)
    STRAVA_CLIENT_ID = get_credential("STRAVA_CLIENT_ID")
    STRAVA_REFRESH_TOKEN = get_credential("STRAVA_REFRESH_TOKEN")
    
    if STRAVA_CLIENT_ID and STRAVA_REFRESH_TOKEN:
        try:
            strava_tool = StravaTool()  # Always recreate to get fresh token
            logger.info("Strava tool initialized successfully")
        except Exception as e:
            logger.error(f"Strava init failed: {e}")
    else:
        logger.info("Strava skipped (missing credentials)")

    # Code Executor
    if has_docker:
        try:
            if not GLOBAL_CODE_EXECUTOR:
                GLOBAL_CODE_EXECUTOR = CodeExecutor()
                logger.info("CodeExecutor initialized successfully")
        except Exception as e:
            logger.error(f"CodeExecutor init failed: {e}")
    else:
        logger.warning("CodeExecutor skipped (docker module not found)")

async def process_code_execution_tags(text: str) -> str:
    """Process [EXEC_CODE:language]code[/EXEC_CODE] tags in AI response"""
    import re
    
    if not GLOBAL_CODE_EXECUTOR:
        return text
    
    pattern = r'\[EXEC_CODE:(\w+)\](.*?)\[/EXEC_CODE\]'
    
    def replace_code_tag(match):
        language = match.group(1)
        code = match.group(2).strip()
        
        try:
            if language == "python":
                result = GLOBAL_CODE_EXECUTOR.run_code(code, "python")
            elif language in ["bash", "shell", "sh"]:
                result = GLOBAL_CODE_EXECUTOR.run_command(code)
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


# =========== ENDPOINTS ===========

@router.get("/status")
async def get_status():
    """Returns system status including active agents"""
    init_tools()
    
    agents = []
    
    # Check Garmin
    if garmin_tool:
        agents.append({"name": "Garmin Coach", "status": "Connected", "type": "health"})
    
    # Check Strava
    if strava_tool:
        agents.append({"name": "Strava Tracker", "status": "Connected", "type": "health"})
    
    # Add other known services (safely check if they exist)
    try:
        from app.services.voice_service import voice_service
        if voice_service:
            agents.append({"name": "Voice Service", "status": "Active", "type": "voice"})
    except:
        pass
    
    try:
        from app.services.proactive_service import proactive_service
        if proactive_service and hasattr(proactive_service, 'running') and proactive_service.running:
            agents.append({"name": "Proactive Service", "status": "Active", "type": "automation"})
        elif proactive_service:
            agents.append({"name": "Proactive Service", "status": "Idle", "type": "automation"})
    except:
        pass
    
    return {
        "system": "operational",
        "agents": agents
    }

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    session_id: str


@router.get("/api/settings")
async def get_settings():
    """Fetches all settings from database."""
    try:
        db_settings = get_db_settings()
        return db_settings
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return {"error": str(e)}


@router.post("/api/settings")
async def update_setting(payload: dict):
    """Updates a single setting in the database."""
    try:
        key = payload.get("key")
        value = payload.get("value")
        
        if not key:
            return {"success": False, "message": "Missing key"}
        
        save_db_setting(key, value)
        logger.info(f"Setting updated: {key}")
        return {"success": True, "message": f"{key} updated successfully"}
    
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        return {"success": False, "message": str(e)}


@router.get("/api/prompts")
async def get_prompts():
    """Fetches all prompts from database."""
    try:
        prompts = get_db_prompts()
        return prompts  # Return directly instead of {"prompts": prompts}
    except Exception as e:
        logger.error(f"Error fetching prompts: {e}")
        return {"error": str(e)}


@router.post("/api/prompts")
async def save_prompt(payload: dict):
    """Saves a prompt to database."""
    try:
        key = payload.get("key")
        value = payload.get("value")
        
        if not key or not value:
            return {"success": False, "message": "Missing key or value"}
        
        save_db_prompt(key, value)
        logger.info(f"Prompt saved: {key}")
        return {"success": True, "message": f"Prompt '{key}' saved"}
    
    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        return {"success": False, "message": str(e)}


@router.get("/api/models")
async def get_models():
    """Fetches available models dynamically with 5-minute TTL cache."""
    global _model_cache
    
    # Check cache first
    now = time.time()
    if now - _model_cache["timestamp"] < CACHE_TTL and _model_cache["data"]:
        logger.debug(f"Returning cached models ({len(_model_cache['data'])} models)")
        return {"data": _model_cache["data"], "cached": True}
    
    try:
        models = []
        
        # Google Models
        try:
            import google.generativeai as genai
            GOOGLE_API_KEY = get_credential("GOOGLE_API_KEY")
            if GOOGLE_API_KEY:
                genai.configure(api_key=GOOGLE_API_KEY)
                google_models = genai.list_models()
                for m in google_models:
                    if hasattr(m, 'name') and 'models/' in m.name:
                        model_id = m.name.replace('models/', '')
                        models.append({
                            "id": model_id,
                            "name": f"Google: {model_id}",
                            "provider": "google"
                        })
        except Exception as e:
            logger.error(f"Failed to fetch Google models: {e}")

        # OpenAI Models
        try:
            OPENAI_API_KEY = get_credential("OPENAI_API_KEY")
            if OPENAI_API_KEY:
                url = "https://api.openai.com/v1/models"
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    for m in data.get("data", []):
                        if "gpt" in m["id"].lower():
                            models.append({
                                "id": m["id"],
                                "name": f"OpenAI: {m['id']}",
                                "provider": "openai"
                            })
        except Exception as e:
            logger.error(f"Failed to fetch OpenAI models: {e}")

        # Ollama Models
        try:
            OLLAMA_URL = get_credential("OLLAMA_URL") or "http://localhost:11434"
            url = f"{OLLAMA_URL}/api/tags"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                for m in data.get("models", []):
                    models.append({
                        "id": m["name"],
                        "name": f"Ollama: {m['name']}",
                        "provider": "ollama"
                    })
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")

        # Update cache
        _model_cache = {"data": models, "timestamp": time.time()}
        logger.info(f"Fetched {len(models)} models from providers (cached for 5 min)")
        
        return {"data": models, "cached": False}
    
    except Exception as e:
        logger.error(f"Critical error in get_models endpoint: {e}", exc_info=True)
        return {"data": [], "error": f"Failed to fetch models: {str(e)}", "cached": False}


@router.post("/api/integrations/garmin/reconnect")
async def reconnect_garmin():
    """Forces Garmin re-authentication by clearing tokens and re-initializing."""
    global garmin_tool, cached_garmin_data, last_garmin_fetch
    import shutil
    import os
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    token_dir = os.path.join(BASE_DIR, "config", "garmin_tokens")
    
    try:
        # 1. Clear tokens
        if os.path.exists(token_dir):
            try:
                shutil.rmtree(token_dir)
                logger.info(f"Cleared Garmin tokens at {token_dir}")
            except OSError as e:
                logger.error(f"Failed to remove token directory: {e}", exc_info=True)
                return {"success": False, "message": f"Failed to clear tokens: {str(e)}"}
            
        # 2. Re-init tool (which triggers login)
        try:
            garmin_tool = GarminCoach()
        except Exception as e:
            logger.error(f"Failed to initialize GarminCoach: {e}", exc_info=True)
            return {"success": False, "message": f"Failed to initialize Garmin client: {str(e)}"}
        
        # 3. Clear cache to force new fetch
        cached_garmin_data = None
        last_garmin_fetch = 0
        
        # 4. Verify login
        if garmin_tool and garmin_tool.client:
             logger.info("Garmin re-connected successfully")
             return {"success": True, "message": "Garmin re-connected successfully!"}
        else:
             logger.warning("Garmin login failed - check credentials in database")
             return {"success": False, "message": "Failed to login. Check credentials in Settings."}
             
    except Exception as e:
        logger.error(f"Unexpected error in reconnect_garmin: {e}", exc_info=True)
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with AI model integration."""
    init_tools()  # Initialize tools if needed
    
    model_id = request.model
    messages = request.messages
    session_id = request.session_id
    
    # Get last user message
    user_msg = messages[-1].content if messages else ""
    
    # --- FETCH GARMIN DATA ---
    global cached_garmin_data, last_garmin_fetch
    
    garmin_triggers = ["garmin", "träning", "sömn", "steg", "puls", "hälsa"]
    if garmin_tool and any(t in user_msg.lower() for t in garmin_triggers):
        now = time.time()
        if (now - last_garmin_fetch > 300) or not cached_garmin_data:
            try:
                data = garmin_tool.get_health_summary()
                if data and not data.get("error"):
                    cached_garmin_data = data
                    last_garmin_fetch = now
            except Exception as e:
                logger.error(f"Garmin fetch failed: {e}")

    # --- FETCH STRAVA DATA ---
    global cached_strava_data, last_strava_fetch
    
    strava_triggers = ["strava", "löpning", "cykling", "pass", "träning", "aktivitet"]
    if strava_tool and any(t in user_msg.lower() for t in strava_triggers):
        now = time.time()
        if (now - last_strava_fetch > 300) or not cached_strava_data:
            try:
                # Strava tool is now async
                activities = await strava_tool.get_health_report(limit=3)
                # Only cache if it's a list (not an error dict)
                if activities and isinstance(activities, list):
                    cached_strava_data = activities
                    last_strava_fetch = now
                elif activities and isinstance(activities, dict) and "error" in activities:
                    logger.warning(f"Strava returned error: {activities['error']}")
            except Exception as e:
                logger.error(f"Strava fetch failed: {e}")

    # Prepare conversation history for Gemini
    gemini_history = []
    system_prompt = get_system_prompt()
    
    # Add context if available
    context_parts = []
    if cached_garmin_data:
        context_parts.append(f"GARMIN DATA:\n{json.dumps(cached_garmin_data, indent=2, ensure_ascii=False)}")
    if cached_strava_data:
        logger.info(f"Adding Strava data to context: {len(cached_strava_data)} activities")
        context_parts.append(f"STRAVA DATA:\n{json.dumps(cached_strava_data, indent=2, ensure_ascii=False)}")
    else:
        logger.warning("No Strava data in cache to add to context")
    
    if context_parts:
        context = "\n\n".join(context_parts)
        gemini_history.append({"role": "user", "parts": [f"{system_prompt}\n\nCONTEXT:\n{context}"]})
        gemini_history.append({"role": "model", "parts": ["Jag har tagit emot informationen och är redo att hjälpa dig."]})
    else:
        gemini_history.append({"role": "user", "parts": [system_prompt]})
        gemini_history.append({"role": "model", "parts": ["Okej, jag förstår. Hur kan jag hjälpa dig?"]})
    
    # Add conversation history
    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg.content]})
    
    # Call Gemini API
    try:
        GOOGLE_API_KEY = get_credential("GOOGLE_API_KEY")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Run async if possible, otherwise executor
        loop = asyncio.get_event_loop()
        gmodel = genai.GenerativeModel(model_id)
        final_response = await loop.run_in_executor(None, lambda: gmodel.generate_content(gemini_history))
        
        # Handle different finish reasons
        if final_response.candidates:
            candidate = final_response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # Log finish reason if not STOP
            if finish_reason != 1:  # 1 = STOP (normal completion)
                logger.warning(f"Gemini finished with reason: {finish_reason}")
            
            # Check if we have text content
            if candidate.content and candidate.content.parts:
                response_text = final_response.text
                
                # Process code execution tags
                response_text = await process_code_execution_tags(response_text)
            else:
                # No text returned - provide helpful error
                reason_map = {
                    1: "STOP",
                    2: "MAX_TOKENS",
                    3: "SAFETY",
                    4: "RECITATION",
                    5: "OTHER",
                    12: "UNKNOWN_REASON_12"
                }
                reason_name = reason_map.get(finish_reason, f"UNKNOWN_{finish_reason}")
                response_text = f"AI kunde inte generera ett svar. Anledning: {reason_name}. Försök omformulera din fråga."
                logger.error(f"Gemini returned no text. Finish reason: {finish_reason} ({reason_name})")
        else:
            response_text = "AI returnerade inget svar. Försök igen."
            logger.error("Gemini response has no candidates")
        
        # Save to DB
        save_message(session_id, "user", user_msg)
        save_message(session_id, "assistant", response_text)
        
        return {"response": response_text}
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {"response": f"Error: {str(e)}"}