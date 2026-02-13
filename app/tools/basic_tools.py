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

@registry.register
async def tool_code_executor(code: str = None, command: str = None, language: str = "python"):
    """
    Executes Python code or Shell commands securely in a Docker container.
    
    Args:
        code: Python code to execute (optional).
        command: Shell command to execute (optional).
        language: Language for code execution (default: python).
    """
    try:
        from app.tools.code_executor import CodeExecutor
        executor = CodeExecutor()
        
        if command:
            logger.info(f"Executing shell command: {command}")
            return executor.run_command(command)
        
        if code:
            logger.info(f"Executing python code: {code[:50]}...")
            return executor.run_code(code, language)
            
        return {"error": "No code or command provided."}
        
    except ImportError:
        return {"error": "Docker module not found. Is python3-docker installed?"}
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        return {"error": str(e)}
