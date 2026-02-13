import asyncio
from typing import Any, Dict

from app.services.tool_registry import registry
from app.tools.definitions import RunPythonCode, WebSearch, GetGarminHealth, GetStravaActivity, GetWeather
from app.core.dependencies import get_code_executor, get_garmin, get_strava
from app.services.web_fallback_service import WebFallbackService

# Initialize helper services (lazy loaded where possible)
_web_service = WebFallbackService()

@registry.register(
    name="run_python_code",
    description="Executes Python code in a safe sandbox. Returns output or error.",
    args_schema=RunPythonCode
)
async def run_python_code_impl(code: str) -> str:
    executor = get_code_executor()
    if not executor:
        return "Error: Code execution environment (Docker) is not available."
    
    try:
        # Use existing executor logic
        result = executor.run_code(code, "python")
        output = result.get("output", "")
        error = result.get("error", "")
        
        if error:
            return f"Error:\n{error}"
        return output or "Code executed successfully (No output)."
    except Exception as e:
        return f"System Error executing code: {e}"

@registry.register(
    name="web_search",
    description="Performs a Google search using SerpAPI. Returns titles, snippets, and URLs.",
    args_schema=WebSearch
)
async def web_search_impl(query: str) -> str:
    try:
        # Use the existing logic from WebFallbackService but exposed as a tool
        # We need a provider instance.
        provider = _web_service._get_search_provider()
        results = await provider.search(query, limit=5)
        
        if not results:
            return "No results found."
            
        formatted = []
        for r in results:
            formatted.append(f"- [{r.title}]({r.url}): {r.snippet}")
            
        return "\n".join(formatted)
    except Exception as e:
        return f"Search failed: {e}"

@registry.register(
    name="get_garmin_health",
    description="Fetches Garmin health metrics (steps, sleep, body battery) for a date.",
    args_schema=GetGarminHealth
)
async def get_garmin_health_impl(date_str: str) -> str:
    # Initialize garmin tool in a thread because it might block (login)
    loop = asyncio.get_event_loop()
    garmin = await loop.run_in_executor(None, get_garmin)
    
    if not garmin:
        return "Garmin service is not configured or unavailable."
    
    # Simple date handling
    import datetime
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        # Fallback to today if parsing fails (robustness)
        target_date = datetime.date.today()
        
    try:
        # We need to ensure we call the synchronous garmin client in a thread if it blocks
        # But for now, we'll assume the dependency manager gave us a client.
        # Ideally, we refactor GarminCoach to be async, but let's wrap it here.
        
        loop = asyncio.get_event_loop()
        # This wrapper function is needed because get_health_report currently fetches 'today' inside.
        # We need to extend GarminCoach to support specific dates or patch it.
        # Looking at GarminCoach code, it calls get_health_report() which hardcodes today.
        
        # ACTUALLY: GarminCoach.get_health_report() takes no args and uses today.
        # We should add a method to GarminCoach or use the client directly.
        # For this refactor, let's stick to 'today' support if the user asks for 'today' 
        # or implement a minimal fetcher here.
        
        # Let's modify GarminCoach later. For now, we only support today/current data efficiently.
        if target_date != datetime.date.today():
             return "Error: Historical data fetching is not yet supported. Ask for today's data."

        data = await loop.run_in_executor(None, garmin.get_health_report)
        import json
        return json.dumps(data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Failed to fetch Garmin data: {e}"


@registry.register(
    name="get_weather",
    description="Fetches weather forecast for configured coordinates using SMHI.",
    args_schema=GetWeather
)
async def get_weather_impl() -> str:
    try:
        from app.tools.weather_core import get_weather
        return await get_weather()
    except Exception as e:
        return f"Failed to fetch weather data: {e}"

@registry.register(
    name="get_strava_activities",
    description="Fetches recent activities from Strava (runs, rides, etc).",
    args_schema=GetStravaActivity
)
async def get_strava_activities_impl(limit: int = 5) -> str:
    try:
        strava_tool = get_strava()
        if not strava_tool:
            return "Strava service is not configured. Add STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN."

        # Re-use existing core logic
        activities = await strava_tool.get_health_report(limit=limit)
        
        # Check for error dict return from core tool
        if isinstance(activities, dict) and "error" in activities:
            return activities["error"]
            
        import json
        return json.dumps(activities, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Failed to fetch Strava activities: {e}"
