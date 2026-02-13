"""Weather tool registrations exposed by the Weather skill."""

# Section: Imports
from app.services.tool_registry import ToolRegistry
from app.tools.definitions import GetWeather


# Section: Registry Hook
def register_tools(registry: ToolRegistry) -> None:
    """Register weather-related tools in the shared tool registry."""

    @registry.register(
        name="get_weather",
        description="Fetches weather forecast for configured coordinates using SMHI.",
        args_schema=GetWeather,
    )
    async def get_weather_impl() -> str:
        # Import inside the function so monkeypatching and lazy loading remain simple.
        from app.tools.weather_core import get_weather

        try:
            return await get_weather()
        except Exception as exc:
            return f"Failed to fetch weather data: {exc}"
