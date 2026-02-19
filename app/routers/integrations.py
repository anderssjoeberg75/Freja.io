from fastapi import APIRouter
from app.core import config
import logging
import os

# Skill helpers
from app.core.dependencies import get_withings
from skills.strava import get_strava_command_processor
from skills.homeassistant.homeassistant_skill import get_homeassistant_command_processor
# Monkeypatch workaround: app.tools.weather_core might not be easily importable if hidden
# But we checked tools.py and it imports it.

logger = logging.getLogger(__name__)
router = APIRouter(tags=["integrations"])

@router.post("/api/integrations/ha/test")
async def test_ha():
    try:
        processor = get_homeassistant_command_processor()
        # Trigger internal client build to check config
        client = processor._build_client()
        # Try a lightweight call
        result = client.list_entities() 
        # API doesn't support limit in list_entities typically, but let's hope it's not huge.
        # Alternatively we can check /api/config or similar if client supports it.
        # But list_entities is what the 'list' command uses, so it's a good test.
        count = len(result) if result else 0
        return {"success": True, "message": f"Connected! Found {count} entities."}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}

@router.post("/api/integrations/weather/test")
async def test_weather():
    try:
        from app.tools.weather_core import get_weather
        data = await get_weather()
        return {"success": True, "message": "Weather data fetched successfully."}
    except ImportError:
         return {"success": False, "message": "Weather tool core not found."}
    except Exception as e:
        return {"success": False, "message": f"Weather fetch failed: {str(e)}"}

@router.post("/api/integrations/strava/test")
async def test_strava():
    try:
        # Check if we have valid tokens
        processor = get_strava_command_processor()
        
        # We try to get a token for the default user (which the callback uses if state is generic)
        # or we just check if the Client ID is set to know if we CAN connect.
        # Real connection test requires a token.
        # Let's try to list activities if possible, or just check 'os.environ' for tokens?
        # Strava implementation usually saves tokens to file/db.
        
        # Simple config check
        if not config.get_credential("STRAVA_CLIENT_ID"):
             return {"success": False, "message": "Client ID is missing."}
             
        return {"success": True, "message": "Configuration valid. (Token verification requires active user session)"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/integrations/withings/test")
async def test_withings():
    try:
        withings = get_withings()
        if not withings:
             return {"success": False, "message": "Withings tool not initialized."}
        
        # Check if client has token
        if withings.client and withings.client.token:
             return {"success": True, "message": "Withings client ready with token."}
        elif config.get_credential("WITHINGS_CLIENT_ID"):
             return {"success": True, "message": "Configuration valid. Click 'Connect' to authenticate."}
        else:
             return {"success": False, "message": "Configuration missing."}
    except Exception as e:
        return {"success": False, "message": str(e)}
