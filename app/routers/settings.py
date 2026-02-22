from fastapi import APIRouter
from app.core import config
from app.core.database import get_db_settings, save_db_setting, get_db_prompts, save_db_prompt
import logging
from google import genai
import time
import httpx
import asyncio
from app.core.config import get_credential, settings
from app.core.settings_schema import SETTINGS_SCHEMA

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache for /api/models (TTL: 5 minutes)
_model_cache = {"data": [], "timestamp": 0}
CACHE_TTL = 300  # 5 minutes

@router.get("/api/settings")
async def get_settings():
    """Fetches all settings from database."""
    try:
        settings = await get_db_settings()
        return settings
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return {"error": str(e)}

@router.get("/api/settings/schema")
async def get_settings_schema():
    """Returns the metadata schema for all available settings."""
    return [item.model_dump() for item in SETTINGS_SCHEMA]

@router.post("/api/settings")
async def update_setting(payload: dict):
    """Updates a single setting in the database."""
    try:
        key = payload.get("key")
        value = payload.get("value")
        
        if not key:
            return {"success": False, "message": "Missing key"}
        
        await save_db_setting(key, value)
        logger.info(f"Setting updated: {key} = ***") # Don't log values for security
        return {"success": True, "message": f"Setting '{key}' updated."}
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        return {"success": False, "message": str(e)}

@router.get("/api/prompts")
async def get_prompts():
    """Fetches all prompts from database."""
    try:
        prompts = await get_db_prompts()
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
        
        await save_db_prompt(key, value)
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

    models = []
    
    # 1. Fetch Gemini Models
    try:
        google_api_key = get_credential("GOOGLE_API_KEY")
        if google_api_key:
            client = genai.Client(api_key=google_api_key)
            for model in client.models.list():
                name = getattr(model, "name", "") or ""
                if name.startswith("models/"):
                    name = name.replace("models/", "", 1)
                if name:
                    models.append(name)
    except Exception as e:
        logger.error(f"Error listing Gemini models: {e}")

    # 2. Fetch Ollama Models
    try:
        ollama_url = get_credential("OLLAMA_URL") or settings.OLLAMA_URL
        # Ensure URL logic (some users might set full API path or just base)
        base_url = ollama_url.rstrip("/")
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for model in data.get("models", []):
                    # Ollama models usually have a 'name' field
                    if "name" in model:
                        models.append(model["name"])
    except Exception as e:
        # Don't log full stack trace for connection errors (common if Ollama is down)
        logger.warning(f"Could not fetch Ollama models: {e}")

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
    
    logger.info(f"Fetched {len(models)} models (Gemini + Ollama)")
    return {"models": models}
