"""Garmin tool registrations exposed by the Garmin skill."""

# Section: Imports
import asyncio
import datetime
import json

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from skills._core.definitions import GetGarminHealth


# Section: Registry Hook
def register_tools(registry: ToolRegistry) -> None:
    """Register Garmin-related tools in the shared tool registry."""

    @registry.register(
        name="get_garmin_health",
        description=(
            "Hämtar daglig Garmin-hälsodata för användaren (INTE träningspass). Anropa detta verktyg AUTOMATISKT när användaren "
            "frågar om sin hälsa, sömn, steg, energi, Body Battery, stress eller puls. "
            "Returnerar: steg, sömnkvalitet, Body Battery, vilopuls, stressnivå, HRV-status mm. "
            "OBS: Använd INTE detta verktyg för att analysera specifika träningspass (använd Strava för det)."
        ),
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

        # Only today is supported – silently fall back to today for other dates
        if target_date != datetime.date.today():
            target_date = datetime.date.today()

        try:
            data = await loop.run_in_executor(None, garmin.get_health_report)
            
            # Fetch advanced metrics and merge them into the data dict
            try:
                adv_data = await loop.run_in_executor(None, garmin.get_advanced_report)
                if isinstance(adv_data, dict) and not adv_data.get("error"):
                    data["advanced_metrics"] = adv_data
            except Exception as adv_e:
                data["advanced_metrics_error"] = str(adv_e)

            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as exc:
            return f"Failed to fetch Garmin data: {exc}"
