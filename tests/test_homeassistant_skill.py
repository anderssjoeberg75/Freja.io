"""Unit tests for Home Assistant skill client and command processing."""

from __future__ import annotations

import httpx
import pytest

from skills.homeassistant.homeassistant_client import HomeAssistantClient, HomeAssistantClientError
from skills.homeassistant.homeassistant_skill import HomeAssistantCommandProcessor


class DummyResponse:
    """Minimal response stub compatible with HomeAssistantClient expectations."""

    def __init__(self, status_code: int, body=None):
        self.status_code = status_code
        self._body = body

    @property
    def content(self):
        return b"" if self._body is None else b"x"

    def json(self):
        return self._body


class DummyClient:
    """Context-manager request stub for monkeypatching httpx.Client."""

    def __init__(self, handler):
        self.handler = handler

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, headers=None, json=None):
        return self.handler(method, url, headers, json)


def patch_httpx_client(monkeypatch, handler):
    """Patch HomeAssistantClient transport layer with a deterministic handler."""

    def factory(*args, **kwargs):
        _ = args, kwargs
        return DummyClient(handler)

    monkeypatch.setattr(httpx, "Client", factory)


def test_list_entities_with_domain_filter(monkeypatch):
    """Entity listing should support domain-only filtering."""
    payload = [
        {"entity_id": "light.kitchen"},
        {"entity_id": "switch.office_lamp"},
        {"entity_id": "light.hall"},
    ]

    def handler(method, url, headers, body):
        assert method == "GET"
        assert url.endswith("/api/states")
        return DummyResponse(200, payload)

    patch_httpx_client(monkeypatch, handler)
    client = HomeAssistantClient("http://ha.local:8123/", "token")

    assert client.list_entities("light") == ["light.kitchen", "light.hall"]


def test_get_state_ok(monkeypatch):
    """State lookup should return Home Assistant state payload as dict."""
    expected = {"entity_id": "light.kitchen", "state": "on", "attributes": {"brightness": 200}}

    def handler(method, url, headers, body):
        assert method == "GET"
        assert url.endswith("/api/states/light.kitchen")
        return DummyResponse(200, expected)

    patch_httpx_client(monkeypatch, handler)
    client = HomeAssistantClient("http://ha.local:8123", "token")

    assert client.get_state("light.kitchen") == expected


def test_call_service_ok(monkeypatch):
    """Service calls should POST payload and return JSON body wrapped in result key."""
    expected = [{"entity_id": "switch.office_lamp", "state": "on"}]

    def handler(method, url, headers, body):
        assert method == "POST"
        assert headers["Content-Type"] == "application/json"
        assert body == {"entity_id": "switch.office_lamp"}
        assert url.endswith("/api/services/switch/turn_on")
        return DummyResponse(200, expected)

    patch_httpx_client(monkeypatch, handler)
    client = HomeAssistantClient("http://ha.local:8123", "token")

    assert client.call_service("switch", "turn_on", {"entity_id": "switch.office_lamp"}) == {"result": expected}


def test_unauthorized_error_message(monkeypatch):
    """401/403 should map to a stable unauthorized user-facing message."""

    def handler(method, url, headers, body):
        return DummyResponse(401, {"message": "unauthorized"})

    patch_httpx_client(monkeypatch, handler)
    client = HomeAssistantClient("http://ha.local:8123", "token")

    with pytest.raises(HomeAssistantClientError, match="Unauthorized – kontrollera HA_TOKEN"):
        client.get_state("light.kitchen")


def test_timeout_error_message(monkeypatch):
    """Timeout exceptions should map to a clear timeout user-facing message."""

    def handler(method, url, headers, body):
        raise httpx.TimeoutException("boom")

    patch_httpx_client(monkeypatch, handler)
    client = HomeAssistantClient("http://ha.local:8123", "token")

    with pytest.raises(HomeAssistantClientError, match="Timeout"):
        client.list_states()


def test_command_parser_service_json_error(monkeypatch):
    """Command parser should return a deterministic response on malformed JSON payload."""

    from app.core.config import settings

    monkeypatch.setattr(settings, "HA_URL", "http://ha.local:8123")
    monkeypatch.setattr(settings, "HA_TOKEN", "token")

    processor = HomeAssistantCommandProcessor()
    import asyncio

    result = asyncio.run(processor.process_message("user-1", "ha service switch turn_on not-json"))

    assert result.handled is True
    assert "Ogiltig JSON payload" in (result.response or "")


def test_command_parser_missing_config_message(monkeypatch):
    """Missing HA config should use the documented variable names in response."""

    from app.core.config import settings

    monkeypatch.setattr(settings, "HA_URL", None)
    monkeypatch.setattr(settings, "HA_TOKEN", None)
    monkeypatch.delenv("HAURL", raising=False)
    monkeypatch.delenv("HATOKEN", raising=False)

    processor = HomeAssistantCommandProcessor()
    import asyncio

    result = asyncio.run(processor.process_message("user-1", "ha list"))

    assert result.handled is True
    assert result.response == (
        "Svar:\nHome Assistant is not configured. Set HAURL and HATOKEN in environment variables."
    )


def test_command_parser_reads_db_backed_ha_base_url(monkeypatch):
    """Command parser should read HA_BASE_URL/HA_TOKEN from DB-backed credentials."""

    import skills.homeassistant.homeassistant_skill as ha_skill_module

    monkeypatch.delenv("HAURL", raising=False)
    monkeypatch.delenv("HATOKEN", raising=False)

    def fake_get_credential(key, fallback=None):
        values = {
            "HA_URL": "",
            "HA_BASE_URL": "http://ha.local:8123",
            "HA_TOKEN": "token",
        }
        return values.get(key, fallback or "")

    monkeypatch.setattr(ha_skill_module, "get_credential", fake_get_credential)

    def handler(method, url, headers, body):
        assert method == "GET"
        assert url.endswith("/api/states")
        return DummyResponse(200, [])

    patch_httpx_client(monkeypatch, handler)

    processor = HomeAssistantCommandProcessor()
    import asyncio

    result = asyncio.run(processor.process_message("user-1", "ha list"))

    assert result.handled is True
    assert result.response == "Svar:\nInga entiteter hittades."


def test_command_parser_reads_legacy_haurl_hatoken_aliases(monkeypatch):
    """Command parser should accept HAURL/HATOKEN aliases when canonical keys are empty."""

    from app.core.config import settings

    monkeypatch.setattr(settings, "HA_URL", None)
    monkeypatch.setattr(settings, "HA_TOKEN", None)
    monkeypatch.setenv("HAURL", "http://ha.local:8123")
    monkeypatch.setenv("HATOKEN", "token")

    def handler(method, url, headers, body):
        assert method == "GET"
        assert url.endswith("/api/states")
        return DummyResponse(200, [])

    patch_httpx_client(monkeypatch, handler)

    processor = HomeAssistantCommandProcessor()
    import asyncio

    result = asyncio.run(processor.process_message("user-1", "ha list"))

    assert result.handled is True
    assert result.response == "Svar:\nInga entiteter hittades."
