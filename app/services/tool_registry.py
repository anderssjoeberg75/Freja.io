from typing import Callable, Any, Dict, List, Type
from pydantic import BaseModel
from app.core.logging import logger
import inspect

class ToolDefinition(BaseModel):
    name: str
    description: str
    args_schema: Type[BaseModel]
    func: Callable

    class Config:
        arbitrary_types_allowed = True

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, args_schema: Type[BaseModel]):
        """Decorator to register a tool with a Pydantic schema."""
        def decorator(func: Callable):
            logger.info(f"Registered tool: {name}")
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                args_schema=args_schema,
                func=func
            )
            return func
        return decorator

    async def execute(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        if tool_name not in self._tools:
            logger.error(f"Tool not found: {tool_name}")
            return f"Error: Tool {tool_name} not found."

        try:
            tool = self._tools[tool_name]
            # Validate args against schema
            # If tool_args is None, treat as empty dict
            tool_args = tool_args or {}
            validated_args = tool.args_schema(**tool_args)
            
            logger.info(f"Executing tool: {tool_name} with {validated_args}")
            
            if inspect.iscoroutinefunction(tool.func):
                return await tool.func(**validated_args.model_dump())
            else:
                return tool.func(**validated_args.model_dump())
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return f"Error executing {tool_name}: {str(e)}"

    def get_gemini_function_declarations(self) -> List[Dict[str, Any]]:
        """Return function definitions in Gemini format."""
        declarations = []
        for name, tool in self._tools.items():
            schema = tool.args_schema.model_json_schema()
            
            # Clean schema (remove 'title' and uppercase 'type')
            def clean_schema(s):
                if isinstance(s, dict):
                    cleaned = {}
                    for k, v in s.items():
                        if k == "title" or k == "default":
                            continue
                        if k == "type" and isinstance(v, str):
                            # Gemini expects uppercase types (STRING, OBJECT, etc.)
                            cleaned[k] = v.upper()
                        else:
                            cleaned[k] = clean_schema(v)
                    return cleaned
                elif isinstance(s, list):
                    return [clean_schema(v) for v in s]
                return s
            
            cleaned_schema = clean_schema(schema)
            
            # Extract properties and cleanup for Gemini
            properties = cleaned_schema.get("properties", {})
            required = cleaned_schema.get("required", [])
            
            function_decl = {
                "name": name,
                "description": tool.description,
                "parameters": {
                    "type": "OBJECT",
                    "properties": properties,
                    "required": required
                }
            }
            declarations.append(function_decl)
        
        return declarations

registry = ToolRegistry()
