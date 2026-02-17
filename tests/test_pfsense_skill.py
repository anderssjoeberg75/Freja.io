"""Tests for pfSense skill registration and reporting."""

import asyncio

from app.services.tool_registry import ToolRegistry
from skills._core.skill_loader import discover_and_register_skills


def test_pfsense_tool_is_registered() -> None:
    """Auto-discovery should register pfSense analysis tool."""
    registry = ToolRegistry()
    discover_and_register_skills(registry)

    assert "analyze_pfsense_logs" in registry._tools


def test_pfsense_tool_returns_report_with_mock(monkeypatch) -> None:
    """Tool should return report text when core function is mocked."""
    registry = ToolRegistry()
    discover_and_register_skills(registry)

    async def fake_report(limit: int = 200, lookback_minutes: int = 60) -> str:
        return (
            "pfSense Log Report\n"
            "- Sampled events: 10\n"
            "- Alerts:\n"
            "  - ⚠️ Event-rate spike detected"
        )

    monkeypatch.setattr("app.tools.pfsense_core.analyze_pfsense_logs", fake_report)

    result = asyncio.run(registry.execute("analyze_pfsense_logs", {"limit": 10, "lookback_minutes": 30}))

    assert isinstance(result, str)
    assert "pfSense Log Report" in result
    assert "Alerts" in result
