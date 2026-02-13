"""Tests for system status agent reporting."""

# Section: Imports
import asyncio

from app.routers import system
from skills._core.skill_types import SkillManifest


# Section: Tests
def test_status_includes_discovered_skills(monkeypatch) -> None:
    """Status endpoint should include discovered skills as active agents."""

    monkeypatch.setattr(system, "get_garmin", lambda: None)
    monkeypatch.setattr(system, "get_strava", lambda: None)
    monkeypatch.setattr(system, "get_code_executor", lambda: None)

    manifests = [
        SkillManifest(name="weather", description="", version="1.0.0"),
        SkillManifest(name="homeassistant", description="", version="1.0.0"),
    ]
    monkeypatch.setattr(system, "discover_and_register_skills", lambda _registry: manifests)

    payload = asyncio.run(system.get_status())
    names = [agent["name"] for agent in payload["agents"]]

    assert "Weather" in names
    assert "Homeassistant" in names
