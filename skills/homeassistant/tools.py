"""Home Assistant tool registrations exposed to the ToolRegistry."""

from __future__ import annotations

import json
import asyncio

from app.core.config import get_credential, settings
from app.services.tool_registry import ToolRegistry
from pydantic import BaseModel, Field
from typing import Optional


# --- Schemas ---

class HACommandSchema(BaseModel):
    command: str = Field(
        ...,
        description=(
            "Home Assistant command. Examples: "
            "'list lights', 'turn on light.kitchen', 'turn off switch.fan', "
            "'get sensor.temperature', 'scene activate scene.evening'"
        ),
    )

class HAServiceSchema(BaseModel):
    domain: str = Field(..., description="HA domain, e.g. 'light', 'switch', 'climate'.")
    service: str = Field(..., description="HA service, e.g. 'turn_on', 'turn_off', 'set_temperature'.")
    entity_id: Optional[str] = Field(None, description="Target entity ID, e.g. 'light.kitchen'.")
    extra: Optional[str] = Field(None, description="Extra JSON payload, e.g. '{\"brightness\": 100}'.")


# --- Helpers ---

def _get_client():
    from skills.homeassistant.homeassistant_client import HomeAssistantClient, HomeAssistantClientError
    ha_url = (
        get_credential("HA_URL")
        or get_credential("HA_BASE_URL")
        or getattr(settings, "HA_URL", "")
        or ""
    ).strip()
    ha_token = (
        get_credential("HA_TOKEN")
        or getattr(settings, "HA_TOKEN", "")
        or ""
    ).strip()
    if not ha_url or not ha_token:
        raise HomeAssistantClientError(
            "Home Assistant ej konfigurerat. Ange HA_URL och HA_TOKEN i inställningarna."
        )
    return HomeAssistantClient(ha_url=ha_url, ha_token=ha_token)


# --- Implementations ---

async def ha_control_impl(command: str) -> str:
    """
    Smart HA controller: parses natural-language commands and calls the right HA API.
    """
    loop = asyncio.get_event_loop()
    try:
        client = _get_client()
    except Exception as e:
        return str(e)

    cmd = command.lower().strip()

    try:
        # list entities
        if cmd.startswith("list"):
            domain = cmd.split()[-1] if len(cmd.split()) > 1 and cmd.split()[-1] != "list" else None
            result = await loop.run_in_executor(None, client.list_entities, domain)
            return "\n".join(result) if result else "Inga entiteter hittades."

        # turn on / off
        if "turn on" in cmd or "sätt på" in cmd or "aktivera" in cmd:
            entity = cmd.split()[-1]
            # Validera entity
            valid_entities = await loop.run_in_executor(None, client.list_entities)
            resolved = client._resolve_entity_id(entity)
            if resolved not in valid_entities:
                return f"Ogiltig entity: {entity}"
            result = await loop.run_in_executor(None, client.turn_on, entity)
            return f"✅ Slog på {entity}"

        if "turn off" in cmd or "stäng av" in cmd or "inaktivera" in cmd:
            entity = cmd.split()[-1]
            valid_entities = await loop.run_in_executor(None, client.list_entities)
            resolved = client._resolve_entity_id(entity)
            if resolved not in valid_entities:
                return f"Ogiltig entity: {entity}"
            result = await loop.run_in_executor(None, client.turn_off, entity)
            return f"✅ Stängde av {entity}"

        # get state
        if "get" in cmd or "status" in cmd or "tillstånd" in cmd:
            entity = cmd.split()[-1]
            valid_entities = await loop.run_in_executor(None, client.list_entities)
            resolved = client._resolve_entity_id(entity)
            if resolved not in valid_entities:
                return f"Ogiltig entity: {entity}"
            state = await loop.run_in_executor(None, client.get_state, entity)
            return json.dumps(state, ensure_ascii=False, indent=2)

        # scene
        if "scene" in cmd or "scen" in cmd:
            scene_id = cmd.split()[-1]
            valid_entities = await loop.run_in_executor(None, client.list_entities, "scene")
            resolved = client._resolve_entity_id(scene_id)
            if resolved not in valid_entities:
                return f"Ogiltig scen: {scene_id}"
            result = await loop.run_in_executor(None, client.trigger_scene, scene_id)
            return f"✅ Aktiverade scen {scene_id}"

        return "Okänt HA-kommando. Exempel: 'turn on light.kitchen', 'list lights', 'get sensor.temp'"

    except Exception as e:
        return f"Home Assistant fel: {e}"


async def ha_service_impl(domain: str, service: str, entity_id: Optional[str] = None, extra: Optional[str] = None) -> str:
    """Call any Home Assistant service directly."""
    loop = asyncio.get_event_loop()
    try:
        client = _get_client()
    except Exception as e:
        return str(e)

    payload: dict = {}
    if entity_id:
        payload["entity_id"] = entity_id
    if extra:
        try:
            payload.update(json.loads(extra))
        except json.JSONDecodeError:
            return f"Ogiltig JSON i extra-parametern: {extra}"

    try:
        result = await loop.run_in_executor(None, client.call_service, domain, service, payload)
        return f"✅ {domain}.{service} utförd: {json.dumps(result, ensure_ascii=False)}"
    except Exception as e:
        return f"Home Assistant fel: {e}"


# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    """Register Home Assistant tools in the shared tool registry."""

    registry.register(
        name="homeassistant_control",
        description=(
            "Kontrollera Home Assistant med ett naturligt kommando. "
            "Använd för att: sätta på/stänga av lampor/kontakter, lista enheter, "
            "aktivera scener, kolla status på sensorer. "
            "Exempel: 'turn on light.kitchen', 'list lights', 'get sensor.temperature_outside'."
        ),
        args_schema=HACommandSchema,
    )(ha_control_impl)

    registry.register(
        name="homeassistant_service",
        description=(
            "Anropa en specifik Home Assistant-tjänst direkt. "
            "Använd när du behöver exakt kontroll, t.ex. 'light turn_on med brightness 80'."
        ),
        args_schema=HAServiceSchema,
    )(ha_service_impl)
