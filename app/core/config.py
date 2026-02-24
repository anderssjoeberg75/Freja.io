import os
from typing import Optional, Set

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env using absolute path (relative to this file) to avoid cwd issues when run as a service
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(_env_path)


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

    USER_NAME: str = "Anders"
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

    VAULT_URL: str = "https://127.0.0.1:8200"
    VAULT_TOKEN: Optional[str] = None
    VAULT_VERIFY: bool = True
    VAULT_MOUNT_POINT: str = "secret"
    VAULT_SECRET_PATH: str = "freja"

    ADMIN_API_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

_SECRET_KEY_HINTS = ("_TOKEN", "_SECRET", "_API_KEY", "PASSWORD", "PASS")

def get_secret_keys() -> Set[str]:
    try:
        from app.core.settings_schema import SETTINGS_SCHEMA
        return {item.key for item in SETTINGS_SCHEMA if item.type == "password"}
    except Exception:
        return set()

def is_secret_key(key: str) -> bool:
    """Best-effort classification of secret keys to avoid storing them in DB."""
    try:
        from app.core.settings_schema import SETTINGS_SCHEMA
        for item in SETTINGS_SCHEMA:
            if item.key == key and item.type == "password":
                return True
    except Exception:
        pass

    upper_key = (key or "").upper()
    return any(hint in upper_key for hint in _SECRET_KEY_HINTS)

def get_credential(key: str, fallback=None) -> str:
    """Get credential from Vault (if secret), DB, then environment values, then fallback."""
    env_value = os.getenv(key)

    if key == "VAULT_TOKEN" and env_value:
        return env_value

    secret_key = is_secret_key(key)

    # Secrets should never be pulled from DB (only Vault or env).
    if secret_key:
        if env_value:
            return env_value
        # pydantic-settings loads .env into settings but NOT into os.environ,
        # so check getattr(settings, key) as a second env fallback.
        settings_value = getattr(settings, key, None)
        if settings_value:
            return settings_value
        try:
            from app.core.vault import get_vault_secret
            vault_val = get_vault_secret(key)
            if vault_val:
                return vault_val
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to read Vault credential for key=%s: %s", key, exc)
        return fallback or ""

    # Non-secret settings: prefer DB, then env, then defaults.
    try:
        from app.core.database import get_db_settings_sync
        db_settings = get_db_settings_sync()
        db_value = db_settings.get(key)
        if db_value:
            return db_value
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to read DB credential for key=%s: %s", key, exc)

    if env_value:
        return env_value

    setting_value = getattr(settings, key, None)
    if setting_value:
        return setting_value

    return fallback or ""


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "db", "mainframe.db")


def get_allowed_origins() -> list[str]:
    """Return normalized CORS origins from settings."""
    raw = (settings.ALLOWED_ORIGINS or "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
