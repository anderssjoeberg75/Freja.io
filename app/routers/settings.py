import os
from fastapi import APIRouter, Depends
from app.core.database import get_db_settings, save_db_setting, get_db_prompts, save_db_prompt
import logging
from google import genai
import time
import httpx
from app.core.config import get_credential, settings, get_secret_keys, is_secret_key
from app.core.settings_schema import SETTINGS_SCHEMA
from app.core.security import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache for /api/models (TTL: 5 minutes)
_model_cache = {"data": [], "timestamp": 0}
CACHE_TTL = 300  # 5 minutes

@router.get("/api/settings", dependencies=[Depends(require_admin)])
async def get_settings():
    """Fetches settings from database and returns secret presence flags."""
    try:
        db_settings = await get_db_settings()
        from app.core.vault import get_all_vault_secrets
        vault_secrets = get_all_vault_secrets()

        # Strip secrets from output (never return secret values to clients)
        public_settings = {k: v for k, v in db_settings.items() if not is_secret_key(k)}

        # Provide a minimal secrets presence map for UI hints
        secrets_present = {}
        secret_keys = get_secret_keys()
        for key in secret_keys:
            if vault_secrets.get(key):
                secrets_present[key] = True
            elif db_settings.get(key):
                # Legacy DB storage (should be migrated away)
                secrets_present[key] = True
            elif os.getenv(key):
                secrets_present[key] = True

        if secrets_present:
            public_settings["__secrets"] = secrets_present

        return public_settings
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return {"error": str(e)}

@router.get("/api/settings/public")
async def get_public_settings():
    """Public settings needed by the client without admin auth."""
    public_keys = ("APP_NAME", "USER_NAME", "SELECTED_MODEL")
    return {key: get_credential(key) for key in public_keys}

@router.get("/api/settings/schema", dependencies=[Depends(require_admin)])
async def get_settings_schema():
    """Returns the metadata schema for all available settings."""
    return [item.model_dump() for item in SETTINGS_SCHEMA]

@router.post("/api/settings", dependencies=[Depends(require_admin)])
async def update_setting(payload: dict):
    """Updates a single setting in the database or Vault."""
    try:
        key = payload.get("key")
        value = payload.get("value")
        
        if not key:
            return {"success": False, "message": "Missing key"}
        
        # Check if setting is a password type to route it to Vault
        is_secret = is_secret_key(key)
        if is_secret:
            if value is None or str(value).strip() == "":
                return {"success": True, "message": f"Ingen ändring för '{key}'."}
            from app.core.vault import save_vault_secret
            success = save_vault_secret(key, str(value))
            if not success:
                logger.error(f"Failed to save secret {key} to Vault")
                return {"success": False, "message": f"Kunde inte spara {key} i Vault. Kontrollera anslutningen."}
        else:
            success = await save_db_setting(key, value)
            if not success:
                logger.error(f"Failed to save setting {key} to database")
                return {"success": False, "message": f"Kunde inte spara {key} i databasen."}
            
        logger.info(f"Setting updated: {key} = ***") # Don't log values for security
        return {"success": True, "message": f"Inställningen '{key}' uppdaterades."}
    except Exception as e:
        logger.error(f"Error updating setting: {e}", exc_info=True)
        return {"success": False, "message": f"Internt fel: {str(e)}"}

@router.get("/api/prompts", dependencies=[Depends(require_admin)])
async def get_prompts():
    """Fetches all prompts from database."""
    try:
        prompts = await get_db_prompts()
        return prompts
    except Exception as e:
        logger.error(f"Error fetching prompts: {e}")
        return {"error": str(e)}

@router.post("/api/prompts", dependencies=[Depends(require_admin)])
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

@router.get("/api/models", dependencies=[Depends(require_admin)])
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
