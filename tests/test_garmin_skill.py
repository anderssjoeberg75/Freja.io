"""Tests for Garmin skill behavior via the shared tool registry."""

# Section: Imports
import asyncio
import datetime

from app.services.tool_registry import ToolRegistry
from skills._core.skill_loader import discover_and_register_skills


# Section: Test fakes
class _FakeGarminCoach:
    """Minimal fake Garmin dependency used for deterministic unit testing."""

    def get_health_report(self):
        return {"steps": 10123, "sleep_hours": 7.5}


# Section: Tests
def test_garmin_skill_execute_returns_json(monkeypatch) -> None:
    """Garmin tool should serialize fake health data to JSON text."""
    registry = ToolRegistry()
    discover_and_register_skills(registry)

    monkeypatch.setattr("app.core.dependencies.get_garmin", lambda: _FakeGarminCoach())

    today = datetime.date.today().isoformat()
    result = asyncio.run(registry.execute("get_garmin_health", {"date_str": today}))

    assert isinstance(result, str)
    assert "steps" in result or "sleep_hours" in result
