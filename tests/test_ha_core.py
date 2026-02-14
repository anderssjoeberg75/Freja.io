"""Unit tests for Home Assistant core helper configuration behavior."""

from __future__ import annotations

import asyncio


def test_resolve_ha_config_prefers_db_keys(monkeypatch):
    """Resolver should use DB-backed HA_URL and HA_TOKEN when available."""

    import app.tools.ha_core as ha_core

    def fake_get_credential(key, fallback=None):
        values = {
            "HA_URL": "http://ha-db.local:8123",
            "HA_BASE_URL": "",
            "HA_TOKEN": "db-token",
        }
        return values.get(key, fallback)

    monkeypatch.setattr(ha_core, "get_credential", fake_get_credential)
    monkeypatch.delenv("HAURL", raising=False)
    monkeypatch.delenv("HATOKEN", raising=False)

    assert ha_core._resolve_ha_config() == ("http://ha-db.local:8123", "db-token")


def test_resolve_ha_config_falls_back_to_legacy_db_and_env(monkeypatch):
    """Resolver should support HA_BASE_URL and HAURL/HATOKEN fallbacks."""

    import app.tools.ha_core as ha_core

    def fake_get_credential(key, fallback=None):
        values = {
            "HA_URL": "",
            "HA_BASE_URL": "http://ha-legacy.local:8123",
            "HA_TOKEN": "",
        }
        return values.get(key, fallback)

    monkeypatch.setattr(ha_core, "get_credential", fake_get_credential)
    monkeypatch.setenv("HATOKEN", "env-token")

    assert ha_core._resolve_ha_config() == ("http://ha-legacy.local:8123", "env-token")


def test_get_ha_state_returns_clear_message_when_not_configured(monkeypatch):
    """State helper should return deterministic message when HA config is missing."""

    import app.tools.ha_core as ha_core

    monkeypatch.setattr(ha_core, "_resolve_ha_config", lambda: ("", ""))

    result = asyncio.run(ha_core.get_ha_state("light.kitchen"))

    assert result == "Home Assistant is not configured. Set HAURL and HATOKEN in environment variables."


def test_resolve_ha_config_supports_db_alias_keys(monkeypatch):
    """Resolver should read HAURL/HATOKEN when DB stores alias keys."""

    import app.tools.ha_core as ha_core

    def fake_get_credential(key, fallback=None):
        values = {
            "HA_URL": "",
            "HA_BASE_URL": "",
            "HAURL": "http://ha-db-alias.local:8123",
            "HA_TOKEN": "",
            "HATOKEN": "db-alias-token",
        }
        return values.get(key, fallback)

    monkeypatch.setattr(ha_core, "get_credential", fake_get_credential)
    monkeypatch.delenv("HAURL", raising=False)
    monkeypatch.delenv("HATOKEN", raising=False)

    assert ha_core._resolve_ha_config() == ("http://ha-db-alias.local:8123", "db-alias-token")
