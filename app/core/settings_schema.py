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
    SettingItem(key="GOOGLE_API_KEY", label="Google API Key", type="password", section="Intelligence", description="Gemini Pro / Flash API Key"),
    SettingItem(
        key="SELECTED_MODEL", 
        label="Selected Model", 
        type="select", 
        section="Intelligence", 
        description="Model used for core logic and analysis"
    ),
    SettingItem(key="OLLAMA_URL", label="Ollama URL", type="text", section="Intelligence", description="e.g. http://127.0.0.1:11434"),
]
