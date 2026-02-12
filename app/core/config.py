from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "DAA Mainframe"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Live voice + vision settings
    GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-native-audio-preview-09-2025"
    LIVE_FRAME_FPS: float = 1.0
    LIVE_AUDIO_CHUNK_MS: int = 30

    # External tool gateway settings
    OPENCLOW_SCHEME: str = "http"
    OPENCLOW_HOST: Optional[str] = None
    OPENCLOW_PORT: Optional[int] = None
    OPENCLOW_PATH: str = "/execute"
    OPENCLOW_TOKEN: Optional[str] = None
    OPENCLOW_TIMEOUT_SECONDS: float = 12.0
    OPENCLOW_RETRIES: int = 1
    
    # Mem0 / Vector DB
    MEM0_API_KEY: Optional[str] = None
    
    # Integrations
    GARMIN_EMAIL: Optional[str] = None
    GARMIN_PASSWORD: Optional[str] = None
    STRAVA_CLIENT_ID: Optional[str] = None
    STRAVA_CLIENT_SECRET: Optional[str] = None
    STRAVA_REFRESH_TOKEN: Optional[str] = None
    
    # Home Assistant
    HA_URL: Optional[str] = None
    HA_TOKEN: Optional[str] = None

    # User / System
    USER_ID: str = "Anders"
    LATITUDE: Optional[str] = None
    LONGITUDE: Optional[str] = None
    
    # LLM / Agents
    OLLAMA_URL: str = "http://127.0.0.1:11434"
    WEB_AGENT_MODEL: str = "gemini-2.5-computer-use-preview-10-2025"
    
    # TTS
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = "21m00Tcm4TlvDq8ikWAM"
    
    # Integrations
    N8N_BASE_URL: Optional[str] = None
    N8N_API_KEY: Optional[str] = None
    
    WITHINGS_CLIENT_ID: Optional[str] = None
    WITHINGS_CLIENT_SECRET: Optional[str] = None
    WITHINGS_REFRESH_TOKEN: Optional[str] = None
    
    # MQTT
    MQTT_BROKER_IP: str = "127.0.0.1"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_BASE: str = "zigbee2mqtt"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# Helper function for DB-first credential loading
def get_credential(key: str, fallback=None) -> str:
    """
    Get credential from database first, then environment variables, then fallback.
    
    Args:
        key: Setting key to retrieve (e.g., "GARMIN_EMAIL")
        fallback: Default value if not found anywhere
    
    Returns:
        The credential value or fallback
    """
    try:
        from app.core.database import get_db_settings
        db_settings = get_db_settings()
        db_value = db_settings.get(key)
        if db_value:
            return db_value
    except Exception:
        pass  # DB not available or error, fall through to env
    
    # Try environment variable via settings object
    env_value = getattr(settings, key, None)
    if env_value:
        return env_value
    
    return fallback or ""


import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "db", "mainframe.db")



def get_allowed_origins() -> list[str]:
    """Return normalized CORS origins from settings."""
    raw = (settings.ALLOWED_ORIGINS or "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
