"""Garmin tool registrations exposed by the Garmin skill."""

# Section: Imports
import asyncio
import datetime
import json

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from app.tools.definitions import GetGarminHealth


# Section: Registry Hook
def register_tools(registry: ToolRegistry) -> None:
    """Register Garmin-related tools in the shared tool registry."""

    @registry.register(
        name="get_garmin_health",
        description="Fetches Garmin health metrics (steps, sleep, body battery) for a date.",
        args_schema=GetGarminHealth,
    )
    async def get_garmin_health_impl(date_str: str) -> str:
        # Initialize Garmin dependency via thread in case login or IO blocks.
        loop = asyncio.get_event_loop()
        garmin = await loop.run_in_executor(None, dependencies.get_garmin)

        if not garmin:
            return "Garmin service is not configured or unavailable."

        try:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.date.today()

        if target_date != datetime.date.today():
            return "Error: Historical data fetching is not yet supported. Ask for today's data."

        try:
            data = await loop.run_in_executor(None, garmin.get_health_report)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as exc:
            return f"Failed to fetch Garmin data: {exc}"
