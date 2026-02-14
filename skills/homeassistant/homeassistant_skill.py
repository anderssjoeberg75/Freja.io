"""Command parsing and orchestration for Home Assistant skill."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from app.core.config import get_credential, settings
from skills.homeassistant.homeassistant_client import HomeAssistantClient, HomeAssistantClientError


@dataclass
class CommandResult:
    """Container indicating if the command parser handled the incoming message."""

    handled: bool
    response: Optional[str] = None


class HomeAssistantCommandProcessor:
    """Parse and execute Home Assistant commands for Telegram and chat inputs."""

    def _build_client(self) -> HomeAssistantClient:
        """Validate configuration and return a ready API client."""
        ha_url = (
            get_credential("HA_URL")
            or get_credential("HA_BASE_URL")
            or settings.HA_URL
            or os.getenv("HAURL")
            or ""
        ).strip()
        ha_token = (get_credential("HA_TOKEN") or settings.HA_TOKEN or os.getenv("HATOKEN") or "").strip()

        if not ha_url or not ha_token:
            raise HomeAssistantClientError(
                "Home Assistant is not configured. Set HA_URL and HA_TOKEN in Settings or environment variables."
            )

        return HomeAssistantClient(ha_url=ha_url, ha_token=ha_token)

    async def process_message(self, user_id: str, text: str) -> CommandResult:
        """Process '/ha' and 'ha' command forms while keeping other messages untouched."""
        _ = user_id  # The current HA API access is global; user-specific scope is not required.
        normalized = text.strip()
        lowered = normalized.lower()

        if lowered.startswith("/ha"):
            command_body = normalized[3:].strip()
            return self._handle_command(command_body)

        if lowered.startswith("ha ") or lowered == "ha":
            command_body = normalized[2:].strip()
            return self._handle_command(command_body)

        return CommandResult(handled=False)

    def _handle_command(self, command_body: str) -> CommandResult:
        """Route Home Assistant command words to concrete client operations."""
        if not command_body:
            return CommandResult(True, "Svar:\nAnvänd: ha list|get|service|on|off|scene")

        parts = command_body.split(maxsplit=3)
        action = parts[0].lower()

        try:
            client = self._build_client()

            if action == "list":
                domain = parts[1] if len(parts) > 1 else None
                entities = client.list_entities(domain=domain)
                if not entities:
                    return CommandResult(True, "Svar:\nInga entiteter hittades.")
                return CommandResult(True, "Svar:\n" + "\n".join(entities))

            if action == "get" and len(parts) > 1:
                state = client.get_state(parts[1])
                return CommandResult(True, f"Svar:\n{json.dumps(state, ensure_ascii=False, indent=2)}")

            if action == "service" and len(parts) >= 3:
                domain = parts[1]
                service = parts[2]
                payload_text = parts[3] if len(parts) == 4 else "{}"
                payload = json.loads(payload_text)
                result = client.call_service(domain=domain, service=service, payload=payload)
                return CommandResult(True, f"Svar:\n{json.dumps(result, ensure_ascii=False, indent=2)}")

            if action == "on" and len(parts) > 1:
                result = client.turn_on(parts[1])
                return CommandResult(True, f"Svar:\n{json.dumps(result, ensure_ascii=False, indent=2)}")

            if action == "off" and len(parts) > 1:
                result = client.turn_off(parts[1])
                return CommandResult(True, f"Svar:\n{json.dumps(result, ensure_ascii=False, indent=2)}")

            if action == "scene" and len(parts) > 1:
                result = client.trigger_scene(parts[1])
                return CommandResult(True, f"Svar:\n{json.dumps(result, ensure_ascii=False, indent=2)}")

            return CommandResult(True, "Svar:\nOkänt HA-kommando. Exempel: ha list, ha get light.kitchen")

        except json.JSONDecodeError:
            return CommandResult(True, "Svar:\nOgiltig JSON payload i service-kommandot.")
        except HomeAssistantClientError as exc:
            return CommandResult(True, f"Svar:\n{exc}")


_processor_singleton: Optional[HomeAssistantCommandProcessor] = None


def get_homeassistant_command_processor() -> HomeAssistantCommandProcessor:
    """Return one singleton processor instance for consistent routing behavior."""
    global _processor_singleton
    if _processor_singleton is None:
        _processor_singleton = HomeAssistantCommandProcessor()
    return _processor_singleton
