"""Tests for weather skill behavior via the shared tool registry."""

# Section: Imports
import asyncio

from app.services.tool_registry import ToolRegistry
from skills._core.skill_loader import discover_and_register_skills


# Section: Tests
def test_weather_skill_execute_returns_forecast_text(monkeypatch) -> None:
    """Weather tool should execute without external network dependency when mocked."""
    registry = ToolRegistry()
    discover_and_register_skills(registry)

    async def fake_get_weather() -> str:
        return "SMHI Forecast: Clear sky"

    monkeypatch.setattr("app.tools.weather_core.get_weather", fake_get_weather)

    result = asyncio.run(registry.execute("get_weather", {}))

    assert isinstance(result, str)
    assert "SMHI" in result or "Forecast" in result
