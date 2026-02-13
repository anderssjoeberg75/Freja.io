"""HTTP client for Home Assistant REST API integration."""

from __future__ import annotations

from typing import Any, Optional

import httpx


class HomeAssistantClientError(Exception):
    """Raised when a Home Assistant request fails with a user-facing message."""


class HomeAssistantClient:
    """Thin client for Home Assistant REST endpoints used by Freja skill commands."""

    def __init__(self, ha_url: str, ha_token: str, timeout_s: int = 15) -> None:
        """Store validated credentials and normalize URL format."""
        self.ha_url = (ha_url or "").rstrip("/")
        self.ha_token = (ha_token or "").strip()
        self.timeout_s = timeout_s

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Execute one HTTP request and map API/network failures to stable error messages."""
        url = f"{self.ha_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.ha_token}",
        }
        if method.upper() == "POST":
            headers["Content-Type"] = "application/json"

        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.request(method=method, url=url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise HomeAssistantClientError("Timeout – Home Assistant svarade inte i tid.") from exc
        except httpx.ConnectError as exc:
            raise HomeAssistantClientError("Connection error – kunde inte nå Home Assistant.") from exc
        except httpx.RequestError as exc:
            raise HomeAssistantClientError("Request error – misslyckades att anropa Home Assistant.") from exc

        if response.status_code in (401, 403):
            raise HomeAssistantClientError("Unauthorized – kontrollera HA_TOKEN.")
        if response.status_code == 404:
            raise HomeAssistantClientError("Not found – kontrollera entity_id eller service.")
        if response.status_code >= 400:
            raise HomeAssistantClientError(f"Home Assistant API error ({response.status_code}).")

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            return None

    def list_states(self) -> list[dict[str, Any]]:
        """Return all states from /api/states."""
        result = self._request("GET", "/api/states")
        return result if isinstance(result, list) else []

    def list_entities(self, domain: str | None = None) -> list[str]:
        """Return entity IDs, optionally filtered by domain prefix."""
        states = self.list_states()
        entity_ids = [str(item.get("entity_id", "")) for item in states if item.get("entity_id")]

        if not domain:
            return entity_ids

        normalized_domain = domain.strip().lower()
        domain_prefix = f"{normalized_domain}."
        return [entity_id for entity_id in entity_ids if entity_id.lower().startswith(domain_prefix)]

    def get_state(self, entity_id: str) -> dict[str, Any]:
        """Return one state object for a specific entity id."""
        result = self._request("GET", f"/api/states/{entity_id}")
        return result if isinstance(result, dict) else {}

    def call_service(self, domain: str, service: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Call a Home Assistant domain/service endpoint and return JSON response."""
        result = self._request("POST", f"/api/services/{domain}/{service}", payload=payload)
        if result is None:
            return None
        return {"result": result}

    def turn_on(self, entity_id: str, **kwargs: Any) -> dict[str, Any] | None:
        """Convenience wrapper for switch/light turn_on."""
        domain = entity_id.split(".", 1)[0]
        payload: dict[str, Any] = {"entity_id": entity_id, **kwargs}
        return self.call_service(domain, "turn_on", payload)

    def turn_off(self, entity_id: str) -> dict[str, Any] | None:
        """Convenience wrapper for switch/light turn_off."""
        domain = entity_id.split(".", 1)[0]
        return self.call_service(domain, "turn_off", {"entity_id": entity_id})

    def set_light(
        self,
        entity_id: str,
        brightness_pct: int | None = None,
        color_temp: int | None = None,
        rgb_color: list[int] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Convenience wrapper for richer light.turn_on payloads."""
        payload: dict[str, Any] = {"entity_id": entity_id, **kwargs}
        if brightness_pct is not None:
            payload["brightness_pct"] = brightness_pct
        if color_temp is not None:
            payload["color_temp"] = color_temp
        if rgb_color is not None:
            payload["rgb_color"] = rgb_color
        return self.call_service("light", "turn_on", payload)

    def trigger_scene(self, entity_id: str) -> dict[str, Any] | None:
        """Convenience wrapper for scene.turn_on calls."""
        return self.call_service("scene", "turn_on", {"entity_id": entity_id})
