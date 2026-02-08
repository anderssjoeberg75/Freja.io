import httpx
from app.core.config import settings
from .formatter import format_temp_for_speech

"""
==============================================================================
FILE: app/tools/ha_core.py
==============================================================================
"""

from app.core.config import settings

HA_URL = settings.HA_URL
HA_TOKEN = settings.HA_TOKEN

async def get_ha_state(entity_id: str):
    """
    Fetches status from Home Assistant and formats temperatures for speech.
    """
    url = f"{HA_URL}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                state = data.get("state")
                unit = data.get("attributes", {}).get("unit_of_measurement", "")

                # If it's a temperature, format for speech
                if unit == "°C" or "temperature" in entity_id.lower():
                    return f"Status för {entity_id} är {format_temp_for_speech(state)}."
                
                return f"Status för {entity_id} är {state} {unit}."
            return f"Kunde inte hitta status för {entity_id}."
        except Exception as e:
            return f"Fel vid anrop till HA: {str(e)}"

async def control_vacuum(entity_id: str, action: str):
    """Controls the vacuum: start, stop, pause, dock."""
    url = f"{HA_URL}/api/services/vacuum/{action}"
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    data = {"entity_id": entity_id}
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=headers, json=data, timeout=5)
            return f"Dammsugaren {action} utförd."
        except:
            return "Kunde inte styra dammsugaren."

async def control_light(entity_id: str, action: str):
    """Controls lighting: on, off."""
    service = "turn_on" if action == "on" else "turn_off"
    url = f"{HA_URL}/api/services/light/{service}"
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    data = {"entity_id": entity_id}
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=headers, json=data, timeout=5)
            return f"Ljuset är nu {action}."
        except:
            return "Kunde inte styra ljuset."