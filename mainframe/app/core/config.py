from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "DAA Mainframe"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
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

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "mainframe.db")
