"""Fitbit tool registrations exposed by the Fitbit skill."""

import json

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from skills._core.definitions import GetFitbitHealth


def register_tools(registry: ToolRegistry) -> None:
    """Register Fitbit-related tools in the shared tool registry."""

    @registry.register(
        name="get_fitbit_health",
        description=(
            "Fetches Fitbit health data including daily activity totals, sleep metrics, "
            "heart rate summary, and recent activities."
        ),
        args_schema=GetFitbitHealth,
    )
    async def get_fitbit_health_impl(activities_limit: int = 5) -> str:
        fitbit_tool = dependencies.get_fitbit()
        if not fitbit_tool:
            return (
                "Fitbit service is not configured. Add FITBIT_CLIENT_ID, "
                "FITBIT_CLIENT_SECRET, and FITBIT_REFRESH_TOKEN."
            )

        data = await fitbit_tool.get_health_report(activities_limit=activities_limit)
        if isinstance(data, dict) and "error" in data:
            return data["error"]

        return json.dumps(data, indent=2, ensure_ascii=False)
