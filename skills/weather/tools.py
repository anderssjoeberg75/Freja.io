"""Weather tool registrations exposed by the Weather skill."""

# Section: Imports
from app.services.tool_registry import ToolRegistry
from skills._core.definitions import GetWeather


# Section: Registry Hook
def register_tools(registry: ToolRegistry) -> None:
    """Register weather-related tools in the shared tool registry."""

    @registry.register(
        name="get_weather",
        description="Fetches weather forecast for configured coordinates using SMHI.",
        args_schema=GetWeather,
    )
    async def get_weather_impl(location: str = None) -> str:
        from skills.weather.core import get_weather

        return await get_weather(location=location)
