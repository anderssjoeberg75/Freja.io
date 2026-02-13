"""Tests for Strava skill behavior via the shared tool registry."""

# Section: Imports
import asyncio

from app.services.tool_registry import ToolRegistry
from skills._core.skill_loader import discover_and_register_skills


# Section: Test fakes
class _FakeStravaTool:
    """Minimal fake Strava dependency used for deterministic unit testing."""

    async def get_health_report(self, limit: int = 5):
        return [{"id": 1, "limit": limit}]


# Section: Tests
def test_strava_skill_execute_returns_json(monkeypatch) -> None:
    """Strava tool should serialize fake activities to JSON text."""
    registry = ToolRegistry()
    discover_and_register_skills(registry)

    monkeypatch.setattr("app.core.dependencies.get_strava", lambda: _FakeStravaTool())

    result = asyncio.run(registry.execute("get_strava_activities", {"limit": 1}))

    assert isinstance(result, str)
    assert "id" in result
