import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "Freja.Io"
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
    TOOL_GATEWAY_SCHEME: str = "http"
    TOOL_GATEWAY_HOST: Optional[str] = None
    TOOL_GATEWAY_PORT: Optional[int] = None
    TOOL_GATEWAY_PATH: str = "/execute"
    TOOL_GATEWAY_TOKEN: Optional[str] = None
    TOOL_GATEWAY_TIMEOUT_SECONDS: float = 12.0
    TOOL_GATEWAY_RETRIES: int = 1
    
    # Mem0 / Vector DB
    MEM0_API_KEY: Optional[str] = None
    
    # Speech-to-text / Telegram voice
    STT_PROVIDER: str = ""
    STT_LANGUAGE_DEFAULT: str = "sv"
    MAX_VOICE_MB: int = 20
    MAX_VOICE_SECONDS: int = 120
    TELEGRAM_VOICE_DOWNLOAD_TIMEOUT_SECONDS: float = 20.0
    TELEGRAM_STT_TIMEOUT_SECONDS: float = 45.0

    # Integrations
    GARMIN_EMAIL: Optional[str] = None
    GARMIN_PASSWORD: Optional[str] = None
    STRAVA_CLIENT_ID: Optional[str] = None
    STRAVA_CLIENT_SECRET: Optional[str] = None
    STRAVA_REDIRECT_URI: Optional[str] = None
    STRAVA_REFRESH_TOKEN: Optional[str] = None
    STRAVA_ACCESS_TOKEN: Optional[str] = None
    STRAVA_MOCK: bool = False
    STRAVA_MOCK_FIXTURE: str = "mixed_run_ride"
    
    # Home Assistant
    HA_URL: Optional[str] = None
    HA_TOKEN: Optional[str] = None

    # User / System
    USER_ID: str = "Anders"
    LATITUDE: Optional[str] = None
    LONGITUDE: Optional[str] = None
    
    # Web fallback
    WEB_FALLBACK_ENABLED: bool = True
    # WEB_FALLBACK_PROVIDER is deprecated, hardcoded to serpapi
    SERPAPI_API_KEY: Optional[str] = None
    WIKIPEDIA_LANG: str = "sv"
    WEB_FALLBACK_MAX_SOURCES: int = 5
    WEB_FALLBACK_CACHE_TTL_MINUTES: int = 20

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
    """Get credential from DB/settings/env with legacy alias support."""

    aliases = {
        "HA_URL": ("HA_BASE_URL", "HAURL"),
        "HA_BASE_URL": ("HA_URL", "HAURL"),
        "HA_TOKEN": ("HATOKEN",),
    }
    candidate_keys = (key, *aliases.get(key, ()))

    try:
        from app.core.database import get_db_settings
        db_settings = get_db_settings()
        for candidate in candidate_keys:
            db_value = db_settings.get(candidate)
            if db_value:
                return str(db_value).strip()
    except Exception:
        pass  # DB not available or error, fall through to settings/env

    for candidate in candidate_keys:
        settings_value = getattr(settings, candidate, None)
        if settings_value:
            return str(settings_value).strip()

        env_value = os.getenv(candidate)
        if env_value:
            return env_value.strip()

    return str(fallback or "").strip()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "db", "mainframe.db")



def get_allowed_origins() -> list[str]:
    """Return normalized CORS origins from settings."""
    raw = (settings.ALLOWED_ORIGINS or "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
