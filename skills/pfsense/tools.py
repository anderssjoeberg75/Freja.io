"""pfSense tool registrations exposed by the pfSense skill."""

from app.services.tool_registry import ToolRegistry
from app.tools.definitions import AnalyzePfSenseLogs


def register_tools(registry: ToolRegistry) -> None:
    """Register pfSense tools in the shared tool registry."""

    @registry.register(
        name="analyze_pfsense_logs",
        description=(
            "Fetches pfSense system logs using pfrest, builds a report, and flags unusual patterns "
            "such as event spikes or critical errors."
        ),
        args_schema=AnalyzePfSenseLogs,
    )
    async def analyze_pfsense_logs_impl(limit: int = 200, lookback_minutes: int = 60) -> str:
        from app.tools.pfsense_core import analyze_pfsense_logs

        try:
            return await analyze_pfsense_logs(limit=limit, lookback_minutes=lookback_minutes)
        except Exception as exc:
            return f"Failed to analyze pfSense logs: {exc}"
