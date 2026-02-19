from pydantic import BaseModel
from typing import List, Optional, Any

class SettingItem(BaseModel):
    key: str
    label: str
    type: str  # text, password, select, action
    section: str
    description: Optional[str] = None
    options: Optional[List[str]] = None
    actionLabel: Optional[str] = None

SETTINGS_SCHEMA: List[SettingItem] = [
    # Identity
    SettingItem(key="APP_NAME", label="App Name", type="text", section="Identity", description="Display name of your instance"),
    SettingItem(key="USER_NAME", label="User Name", type="text", section="Identity", description="How Freja addresses you"),
    
    # Intelligence
    SettingItem(key="GOOGLE_API_KEY", label="Google API Key", type="password", section="Intelligence", description="Gemini Pro / Flash API Key"),
    SettingItem(
        key="GEMINI_LIVE_MODEL", 
        label="Selected Model", 
        type="select", 
        section="Intelligence", 
        description="Model used for core logic and analysis"
        # Options removed to allow dynamic fetching from /api/models
    ),
    SettingItem(key="OLLAMA_URL", label="Ollama URL", type="text", section="Intelligence", description="e.g. http://127.0.0.1:11434"),
    SettingItem(key="SERPAPI_API_KEY", label="SerpAPI Key", type="password", section="Intelligence", description="Get from serpapi.com"),
    SettingItem(key="MEM0_API_KEY", label="Mem0 API Key", type="password", section="Intelligence", description="For conversational memory (app.mem0.ai)"),
    
    # Weather & Location
    SettingItem(key="LATITUDE", label="Latitude", type="text", section="Skill: Weather", description="e.g. 59.3293 (Decimal)"),
    SettingItem(key="LONGITUDE", label="Longitude", type="text", section="Skill: Weather", description="e.g. 18.0686 (Decimal)"),
    SettingItem(key="TIMEZONE", label="Timezone", type="text", section="Skill: Weather", description="e.g. Europe/Stockholm"),

    # Skill: Home Assistant
    SettingItem(key="HA_URL", label="Home Assistant URL", type="text", section="Skill: Home Assistant", description="e.g. http://homeassistant.local:8123"),
    SettingItem(key="HA_TOKEN", label="Home Assistant Token", type="password", section="Skill: Home Assistant", description="Long-lived access token"),
    
    # Skill: Garmin
    SettingItem(key="GARMIN_EMAIL", label="Garmin Email", type="text", section="Skill: Garmin"),
    SettingItem(key="GARMIN_PASSWORD", label="Garmin Password", type="password", section="Skill: Garmin"),
    SettingItem(
        key="GARMIN_RECONNECT", 
        label="Garmin Connection", 
        type="action", 
        section="Skill: Garmin", 
        actionLabel="Test / Reconnect",
        description="Force reconnect if token is expired."
    ),
    
    # Skill: Strava
    SettingItem(key="STRAVA_CLIENT_ID", label="Strava Client ID", type="text", section="Skill: Strava", description="From Strava API settings"),
    SettingItem(key="STRAVA_CLIENT_SECRET", label="Strava Client Secret", type="password", section="Skill: Strava"),
    SettingItem(key="STRAVA_REDIRECT_URI", label="Strava Redirect URI", type="text", section="Skill: Strava"),
    SettingItem(key="STRAVA_REFRESH_TOKEN", label="Strava Refresh Token", type="password", section="Skill: Strava", description="Handled automatically"),
    
    # Skill: Withings
    SettingItem(key="WITHINGS_CLIENT_ID", label="Withings Client ID", type="text", section="Skill: Withings"),
    SettingItem(key="WITHINGS_CLIENT_SECRET", label="Withings Client Secret", type="password", section="Skill: Withings"),
    SettingItem(key="WITHINGS_REDIRECT_URI", label="Withings Redirect URI", type="text", section="Skill: Withings"),
    SettingItem(
        key="WITHINGS_CONNECT", 
        label="Withings Connection", 
        type="action", 
        section="Skill: Withings", 
        actionLabel="Connect Withings",
        description="Click to start authentication flow."
    ),
    SettingItem(key="WITHINGS_REFRESH_TOKEN", label="Withings Refresh Token", type="password", section="Skill: Withings"),
    
    # Skill: Telegram
    SettingItem(key="TELEGRAM_BOT_TOKEN", label="Telegram Bot Token", type="password", section="Skill: Telegram"),
    SettingItem(key="TELEGRAM_CHAT_ID", label="Telegram Chat ID", type="text", section="Skill: Telegram")
]
