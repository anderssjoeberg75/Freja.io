from typing import Callable, Any, Dict, List, Type
from pydantic import BaseModel, ConfigDict
from app.core.logging import logger
import inspect

class ToolDefinition(BaseModel):
    name: str
    description: str
    args_schema: Type[BaseModel]
    func: Callable

    model_config = ConfigDict(arbitrary_types_allowed=True)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, args_schema: Type[BaseModel]):
        """Decorator to register a tool with a Pydantic schema."""
        def decorator(func: Callable):
            if name in self._tools:
                logger.warning("Tool already registered, overriding previous definition: {}", name)
            logger.info("Registered tool: {}", name)
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
            logger.error("Tool not found: {}", tool_name)
            return f"Error: Tool {tool_name} not found."

        try:
            from pydantic import ValidationError as PydanticValidationError
            tool = self._tools[tool_name]
            tool_args = tool_args or {}

            # --- Robustness: clean args before Pydantic validation ---
            # 1. Remove None/null AND empty-string values so schema defaults kick in
            # 2. Remove unknown keys that Pydantic would reject
            schema_fields = set(tool.args_schema.model_fields.keys())
            clean_args = {
                k: v
                for k, v in tool_args.items()
                if v is not None and v != "" and k in schema_fields
            }

            try:
                validated_args = tool.args_schema(**clean_args)
            except PydanticValidationError as ve:
                # Extract missing/invalid field names and return a short, actionable message
                # so the LLM can retry with correct arguments instead of paraphrasing a long error.
                missing = [e["loc"][0] for e in ve.errors() if e.get("loc")]
                msg = f"Tool '{tool_name}' called with missing or invalid required argument(s): {', '.join(str(m) for m in missing)}. Please retry with a valid value."
                logger.warning("Tool validation failed for {}: {}", tool_name, msg)
                return msg

            logger.info("Executing tool: {} with {}", tool_name, validated_args)

            if inspect.iscoroutinefunction(tool.func):
                return await tool.func(**validated_args.model_dump())
            else:
                return tool.func(**validated_args.model_dump())
        except Exception as e:
            logger.exception("Tool execution failed: {}", e)
            return f"Error executing {tool_name}: {str(e)}"

    def get_gemini_function_declarations(self) -> List[Dict[str, Any]]:
        """Return function definitions in Gemini format."""
        declarations = []
        for name, tool in self._tools.items():
            schema = tool.args_schema.model_json_schema()
            
            # Clean schema (remove 'title', 'default', and handle 'anyOf' / uppercase 'type')
            def clean_schema(s):
                if not isinstance(s, dict):
                    if isinstance(s, list):
                        return [clean_schema(v) for v in s]
                    return s

                # 1. Resolve anyOf (Gemini doesn't support it)
                if "anyOf" in s:
                    options = s["anyOf"]
                    # Priority: Non-null type
                    non_null_options = [o for o in options if o.get("type") != "null"]
                    if non_null_options:
                        # Use the first non-null option and merge with current dict (for description, etc.)
                        target = {k: v for k, v in s.items() if k != "anyOf"}
                        target.update(non_null_options[0])
                        return clean_schema(target)
                    elif options:
                        return clean_schema(options[0])

                # 2. Filter and Map
                cleaned = {}
                for k, v in s.items():
                    # Forbidden fields in Gemini Schema
                    if k in ("title", "default", "$defs", "additionalProperties", "anyOf"):
                        continue
                    
                    if k == "type" and isinstance(v, str):
                        cleaned[k] = v.upper()
                    else:
                        cleaned[k] = clean_schema(v)
                return cleaned

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

    def get_ollama_function_declarations(self) -> List[Dict[str, Any]]:
        """Return function definitions in Ollama/OpenAI format."""
        declarations = []
        for name, tool in self._tools.items():
            schema = tool.args_schema.model_json_schema()
            
            # Clean schema for Ollama
            def clean_schema(s):
                if not isinstance(s, dict):
                    if isinstance(s, list):
                        return [clean_schema(v) for v in s]
                    return s

                if "anyOf" in s:
                    options = s["anyOf"]
                    non_null_options = [o for o in options if o.get("type") != "null"]
                    if non_null_options:
                        target = {k: v for k, v in s.items() if k != "anyOf"}
                        target.update(non_null_options[0])
                        return clean_schema(target)
                    elif options:
                        return clean_schema(options[0])

                cleaned = {}
                for k, v in s.items():
                    # Ollama allows standard JSON schema types (lowercase string, integer, etc.)
                    if k in ("title", "default", "$defs", "additionalProperties", "anyOf"):
                        continue
                    cleaned[k] = clean_schema(v)
                return cleaned

            cleaned_schema = clean_schema(schema)
            properties = cleaned_schema.get("properties", {})
            required = cleaned_schema.get("required", [])
            
            # Standard OpenAI format for tools
            function_decl = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            declarations.append(function_decl)
        
        return declarations

registry = ToolRegistry()
