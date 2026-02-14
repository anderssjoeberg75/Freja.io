"""Home Assistant helper tools used by Freja actions."""

from __future__ import annotations

import os

import httpx

from app.core.config import get_credential
from .formatter import format_temp_for_speech


def _resolve_ha_config() -> tuple[str, str]:
    """Resolve Home Assistant URL/token using DB-first credentials with env fallbacks."""
    ha_url = str(get_credential("HA_URL", "") or "").strip()
    if not ha_url:
        ha_url = str(get_credential("HA_BASE_URL", "") or "").strip()
    if not ha_url:
        ha_url = str(get_credential("HAURL", "") or "").strip()
    if not ha_url:
        ha_url = (os.getenv("HAURL") or "").strip()

    ha_token = str(get_credential("HA_TOKEN", "") or "").strip()
    if not ha_token:
        ha_token = str(get_credential("HATOKEN", "") or "").strip()
    if not ha_token:
        ha_token = (os.getenv("HATOKEN") or "").strip()

    return ha_url, ha_token


def _get_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


async def get_ha_state(entity_id: str):
    """Fetch state from Home Assistant and format temperatures for speech."""
    ha_url, ha_token = _resolve_ha_config()
    if not ha_url or not ha_token:
        return "Home Assistant is not configured. Set HAURL and HATOKEN in environment variables."

    url = f"{ha_url}/api/states/{entity_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=_get_headers(ha_token), timeout=5)
            if response.status_code == 200:
                data = response.json()
                state = data.get("state")
                unit = data.get("attributes", {}).get("unit_of_measurement", "")

                if unit == "°C" or "temperature" in entity_id.lower():
                    return f"Status för {entity_id} är {format_temp_for_speech(state)}."

                return f"Status för {entity_id} är {state} {unit}."
            return f"Kunde inte hitta status för {entity_id}."
        except Exception as exc:  # Keep broad catch to preserve user-facing fallback behavior.
            return f"Fel vid anrop till HA: {exc}"


async def control_vacuum(entity_id: str, action: str):
    """Control the vacuum with Home Assistant service actions."""
    ha_url, ha_token = _resolve_ha_config()
    if not ha_url or not ha_token:
        return "Home Assistant is not configured. Set HAURL and HATOKEN in environment variables."

    url = f"{ha_url}/api/services/vacuum/{action}"
    data = {"entity_id": entity_id}

    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=_get_headers(ha_token), json=data, timeout=5)
            return f"Dammsugaren {action} utförd."
        except Exception:
            return "Kunde inte styra dammsugaren."


async def control_light(entity_id: str, action: str):
    """Control light state through Home Assistant service calls."""
    ha_url, ha_token = _resolve_ha_config()
    if not ha_url or not ha_token:
        return "Home Assistant is not configured. Set HAURL and HATOKEN in environment variables."

    service = "turn_on" if action == "on" else "turn_off"
    url = f"{ha_url}/api/services/light/{service}"
    data = {"entity_id": entity_id}

    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=_get_headers(ha_token), json=data, timeout=5)
            return f"Ljuset är nu {action}."
        except Exception:
            return "Kunde inte styra ljuset."
