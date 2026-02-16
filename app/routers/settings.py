from fastapi import APIRouter
from app.core import config
from app.core.database import get_db_settings, save_db_setting, get_db_prompts, save_db_prompt
import logging
import google.generativeai as genai
import time
from app.core.config import get_credential
<<<<<<< HEAD
=======
from app.core.settings_schema import SETTINGS_SCHEMA
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache for /api/models (TTL: 5 minutes)
_model_cache = {"data": [], "timestamp": 0}
CACHE_TTL = 300  # 5 minutes

@router.get("/api/settings")
async def get_settings():
    """Fetches all settings from database."""
    try:
        settings = get_db_settings()
        return settings
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return {"error": str(e)}

<<<<<<< HEAD
=======
@router.get("/api/settings/schema")
async def get_settings_schema():
    """Returns the metadata schema for all available settings."""
    return [item.model_dump() for item in SETTINGS_SCHEMA]

>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
@router.post("/api/settings")
async def update_setting(payload: dict):
    """Updates a single setting in the database."""
    try:
        key = payload.get("key")
        value = payload.get("value")
        
        if not key:
            return {"success": False, "message": "Missing key"}
        
        save_db_setting(key, value)
        logger.info(f"Setting updated: {key} = ***") # Don't log values for security
        return {"success": True, "message": f"Setting '{key}' updated."}
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        return {"success": False, "message": str(e)}

@router.get("/api/prompts")
async def get_prompts():
    """Fetches all prompts from database."""
    try:
        prompts = get_db_prompts()
        return prompts
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

    current_time = time.time()
    
    # Return cached data if valid
    if _model_cache["data"] and (current_time - _model_cache["timestamp"] < CACHE_TTL):
        return {"models": _model_cache["data"]}

    try:
        GOOGLE_API_KEY = get_credential("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            return {"models": []}

        genai.configure(api_key=GOOGLE_API_KEY)
        
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                models.append(name)
        
        # Sort and deduplicate
        models = sorted(list(set(models)), reverse=True)
        
        # Default fallback if empty
        if not models:
            models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
            
        # Update cache
        _model_cache = {
            "data": models,
            "timestamp": current_time
        }
        
        logger.info(f"Fetched {len(models)} models from Google API")
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        # Return fallback cache or hardcoded list on error
        if _model_cache["data"]:
             return {"models": _model_cache["data"]}
        return {"models": ["gemini-2.0-flash", "gemini-1.5-pro"]}
