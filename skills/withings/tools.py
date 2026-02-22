"""Withings tool registrations exposed by the Withings skill."""

# Section: Imports
import asyncio
import json

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from skills._core.definitions import GetWithingsHealth


# Section: Registry Hook
def register_tools(registry: ToolRegistry) -> None:
    """Register Withings-related tools in the shared tool registry."""

    @registry.register(
        name="get_withings_health",
        description="Retrieves Withings health data (weight/vikt, fat percentage, muscle mass) for the user. Use for questions like 'vad väger jag?', 'min vikt' or body composition.",
        args_schema=GetWithingsHealth,
    )
    async def get_withings_health_impl() -> str:
        # Initialize Withings dependency
        loop = asyncio.get_event_loop()
        withings = await loop.run_in_executor(None, dependencies.get_withings)

        if not withings:
            return "Withings service is not configured or unavailable. Check client ID and refresh token."

        try:
            data = await loop.run_in_executor(None, withings.get_health_report)
            if isinstance(data, str):
                return data
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as exc:
            return f"Failed to fetch Withings data: {exc}"
