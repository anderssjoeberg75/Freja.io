"""Strava tool registrations exposed by the Strava skill."""

# Section: Imports
import json

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from skills._core.definitions import GetStravaActivity


# Section: Registry Hook
def register_tools(registry: ToolRegistry) -> None:
    """Register Strava-related tools in the shared tool registry."""

    @registry.register(
        name="get_strava_activities",
        description=(
            "Hämtar de senaste träningspassen från Strava (löpning, cykling, promenader etc). "
            "Använd detta verktyg när användaren frågar om specifika träningspass, "
            "träningsanalys, distans, fart, eller senaste rundan."
        ),
        args_schema=GetStravaActivity,

    )
    async def get_strava_activities_impl(limit: int = 5) -> str:
        try:
            strava_tool = dependencies.get_strava()
            if not strava_tool:
                return (
                    "Strava service is not configured. Add STRAVA_CLIENT_ID, "
                    "STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN."
                )

            activities = await strava_tool.get_health_report(limit=limit)
            if isinstance(activities, dict) and "error" in activities:
                return activities["error"]

            return json.dumps(activities, indent=2, ensure_ascii=False)
        except Exception as exc:
            return f"Failed to fetch Strava activities: {exc}"
