import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Freja.Io"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-native-audio-preview-09-2025"
    LIVE_FRAME_FPS: float = 1.0
    LIVE_AUDIO_CHUNK_MS: int = 30

    TOOL_GATEWAY_SCHEME: str = "http"
    TOOL_GATEWAY_HOST: Optional[str] = None
    TOOL_GATEWAY_PORT: Optional[int] = None
    TOOL_GATEWAY_PATH: str = "/execute"
    TOOL_GATEWAY_TOKEN: Optional[str] = None
    TOOL_GATEWAY_TIMEOUT_SECONDS: float = 12.0
    TOOL_GATEWAY_RETRIES: int = 1

    MEM0_API_KEY: Optional[str] = None

    STT_PROVIDER: str = ""
    STT_LANGUAGE_DEFAULT: str = "sv"
    MAX_VOICE_MB: int = 20
    MAX_VOICE_SECONDS: int = 120
    TELEGRAM_VOICE_DOWNLOAD_TIMEOUT_SECONDS: float = 20.0
    TELEGRAM_STT_TIMEOUT_SECONDS: float = 45.0

    GARMIN_EMAIL: Optional[str] = None
    GARMIN_PASSWORD: Optional[str] = None
    STRAVA_CLIENT_ID: Optional[str] = None
    STRAVA_CLIENT_SECRET: Optional[str] = None
    STRAVA_REDIRECT_URI: Optional[str] = None
    STRAVA_REFRESH_TOKEN: Optional[str] = None
    STRAVA_ACCESS_TOKEN: Optional[str] = None
    STRAVA_MOCK: bool = False
    STRAVA_MOCK_FIXTURE: str = "mixed_run_ride"

    HA_URL: Optional[str] = None
    HA_TOKEN: Optional[str] = None

    USER_ID: str = "Anders"
    LATITUDE: Optional[str] = None
    LONGITUDE: Optional[str] = None
    TIMEZONE: str = "Europe/Stockholm"

    WEB_FALLBACK_ENABLED: bool = True
    SERPAPI_API_KEY: Optional[str] = None
    WIKIPEDIA_LANG: str = "sv"
    WEB_FALLBACK_MAX_SOURCES: int = 5
    WEB_FALLBACK_CACHE_TTL_MINUTES: int = 20

    OLLAMA_URL: str = "http://127.0.0.1:11434"
    WEB_AGENT_MODEL: str = "gemini-2.5-computer-use-preview-10-2025"

    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = "21m00Tcm4TlvDq8ikWAM"

    N8N_BASE_URL: Optional[str] = None
    N8N_API_KEY: Optional[str] = None

    WITHINGS_CLIENT_ID: Optional[str] = None
    WITHINGS_CLIENT_SECRET: Optional[str] = None
    WITHINGS_REDIRECT_URI: Optional[str] = None
    WITHINGS_REFRESH_TOKEN: Optional[str] = None

    MQTT_BROKER_IP: str = "127.0.0.1"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_BASE: str = "zigbee2mqtt"

    SELECTED_MODEL: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    HA_ALIASES: str = "{}"

    VAULT_URL: str = "http://127.0.0.1:8200"
    VAULT_TOKEN: Optional[str] = None
    VAULT_MOUNT_POINT: str = "secret"
    VAULT_SECRET_PATH: str = "freja"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()


def get_credential(key: str, fallback=None) -> str:
    """Get credential from Vault (if secret), DB, then environment values, then fallback."""
    try:
        from app.core.settings_schema import SETTINGS_SCHEMA
        is_secret = any(item.key == key and item.type == "password" for item in SETTINGS_SCHEMA)
        if is_secret:
            from app.core.vault import get_vault_secret
            vault_val = get_vault_secret(key)
            if vault_val:
                return vault_val
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to read Vault credential for key=%s: %s", key, exc)

    try:
        from app.core.database import get_db_settings_sync

        db_settings = get_db_settings_sync()
        db_value = db_settings.get(key)
        if db_value:
            return db_value
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to read DB credential for key=%s: %s", key, exc)

    env_value = getattr(settings, key, None)
    if env_value:
        return env_value

    return fallback or ""


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "db", "mainframe.db")


def get_allowed_origins() -> list[str]:
    """Return normalized CORS origins from settings."""
    raw = (settings.ALLOWED_ORIGINS or "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
