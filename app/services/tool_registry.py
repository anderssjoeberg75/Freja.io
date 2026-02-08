from typing import Callable, Any, Dict, List
from pydantic import BaseModel
from app.core.logging import logger
import inspect

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict
    func: Callable

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        
    def register(self, tool_func: Callable):
        """Decorator to register a tool."""
        # Extract metadata from function docstring/signature
        # For simplicity in this iteration, we require manual definition or Pydantic models separately
        # But let's do a basic inspection
        name = tool_func.__name__
        logger.info(f"Registered tool: {name}")
        self._tools[name] = ToolDefinition(
            name=name,
            description=tool_func.__doc__ or "No description",
            parameters={}, # TODO: Introspect Pydantic models
            func=tool_func
        )
        return tool_func

    async def execute(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self._tools:
            logger.error(f"Tool not found: {tool_name}")
            return f"Error: Tool {tool_name} not found."
            
        try:
            tool = self._tools[tool_name]
            logger.info(f"Executing tool: {tool_name} with {kwargs}")
            if inspect.iscoroutinefunction(tool.func):
                return await tool.func(**kwargs)
            else:
                return tool.func(**kwargs)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def get_definitions(self) -> List[dict]:
        """Return tool definitions in Gemini/OpenAI format."""
        # TODO: Return actual schema
        return []

registry = ToolRegistry()

# --- Example Tool ---
@registry.register
async def get_weather(location: str):
    """Get current weather for a location."""
    return f"Weather in {location} is Sunny, 25°C"
