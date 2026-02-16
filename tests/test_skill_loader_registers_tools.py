"""Tests for auto-discovery skill tool registration."""

# Section: Imports
from app.services.tool_registry import ToolRegistry
from skills._core.skill_loader import discover_and_register_skills


# Section: Tests
def test_skill_loader_registers_expected_tools() -> None:
    """Discovering skills should register weather, garmin, strava, and roborock tools."""
    registry = ToolRegistry()
    discover_and_register_skills(registry)

    assert "get_weather" in registry._tools
    assert "get_garmin_health" in registry._tools
    assert "get_strava_activities" in registry._tools
<<<<<<< HEAD
    assert "roborock_start" in registry._tools
=======
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
