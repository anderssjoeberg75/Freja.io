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
            "frågar om sin hälsa, sömn, steg, energi, Body Battery, stress, puls eller ber dig 'analysera', 'analysera min garmin data'. "
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

            result_string = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Explicit instruction for the LLM to prevent it from just defining the JSON structure
            llm_instruction = (
                "\n\n[SYSTEM INSTRUCTION]: The above is the user's health data from Garmin. "
                "You MUST act as an expert health coach and analyze the actual VALUES "
                "(like sleep, stress, body battery, HRV, etc.) to give the user personalized advice and insights. "
                "CRITICAL INSTRUCTION: You MUST specifically mention and analyze any 'advanced_metrics' that are present, such as VO2 Max, Respiration (Andning), Endurance Score (Uthållighetspoäng), or Training Status. Do not ignore them. "
                "DO NOT explain what the JSON keys mean. DO NOT say 'This is a JSON object'. "
                "Answer directly in a natural, coaching tone in Swedish."
            )
            
            return result_string + llm_instruction
            
        except Exception as exc:
            return f"Failed to fetch Garmin data: {exc}"
