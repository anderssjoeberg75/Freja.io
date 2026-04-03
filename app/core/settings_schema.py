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
    # Intelligence Core

    SettingItem(
        key="SELECTED_MODEL", 
        label="Selected Model", 
        type="select", 
        section="Intelligence", 
        description="Model used for core logic and analysis"
    ),
    SettingItem(key="OLLAMA_URL", label="Ollama URL", type="text", section="Intelligence", description="e.g. http://127.0.0.1:11434"),
    
    # Fitbit (Dynamically loaded by UI, but schema needed for backend validation)
    SettingItem(key="FITBIT_CLIENT_ID", label="Fitbit Client ID", type="text", section="Health"),
    SettingItem(key="FITBIT_CLIENT_SECRET", label="Fitbit Client Secret", type="password", section="Health"),
    SettingItem(key="FITBIT_REDIRECT_URI", label="Fitbit Redirect URI", type="text", section="Health"),
    SettingItem(key="FITBIT_REFRESH_TOKEN", label="Fitbit Refresh Token", type="password", section="Health"),
]
