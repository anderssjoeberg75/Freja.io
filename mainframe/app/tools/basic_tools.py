from app.services.tool_registry import registry
from app.core.logging import logger

@registry.register
async def get_weather(location: str):
    """
    Get current weather for a specific location.
    
    Args:
        location: City name or coordinates.
    """
    # Mock implementation
    logger.info(f"Getting weather for {location}")
    return f"Weather in {location} is currently Sunny, 22°C. Wind: 12km/h SE."

@registry.register
async def web_search(query: str):
    """
    Perform a web search using the Web Agent.
    
    Args:
        query: The search query.
    """
    # Placeholder for Playwright agent
    logger.info(f"Searching web for: {query}")
    return f"Search Results for '{query}': [Mock Result 1] [Mock Result 2]"

@registry.register
async def get_system_status():
    """Returns the current health and status of the Mainframe."""
    return {
        "cpu": "12%",
        "memory": "4.2GB/16GB",
        "active_services": ["voice", "llm", "proactive"]
    }
