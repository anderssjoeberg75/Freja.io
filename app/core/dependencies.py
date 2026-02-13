from functools import lru_cache
from typing import Optional
from app.core.logging import logger
from app.core.config import get_credential

# Lazy imports to avoid circular dependencies
# We import inside functions or use string forward references if needed

class DependencyManager:
    """
    Manages singleton instances of tools and services.
    Replaces global variables in api.py.
    """
    def __init__(self):
        self._garmin_tool = None
        self._strava_tool = None
        self._code_executor = None
        self._has_docker = False
        
        # Check for Docker support once
        try:
            import app.tools.code_executor
            self._has_docker = True
        except ImportError:
            self._has_docker = False

    def get_garmin_tool(self):
        if self._garmin_tool:
            return self._garmin_tool
            
        # Try to initialize
        GARMIN_EMAIL = get_credential("GARMIN_EMAIL")
        GARMIN_PASSWORD = get_credential("GARMIN_PASSWORD")
        
        if GARMIN_EMAIL and GARMIN_PASSWORD:
            try:
                from app.tools.garmin_core import GarminCoach
                self._garmin_tool = GarminCoach()
                logger.info("Garmin tool initialized (Dependency)")
            except Exception as e:
                logger.error(f"Garmin init failed: {e}")
        
        return self._garmin_tool

    def get_strava_tool(self):
        # Strava tool needs fresh token often, but let's cache the instance 
        # and let the tool handle token refresh internally if possible.
        # Alternatively, we recreate it if credentials change.
        if self._strava_tool:
            return self._strava_tool

        STRAVA_CLIENT_ID = get_credential("STRAVA_CLIENT_ID")
        STRAVA_REFRESH_TOKEN = get_credential("STRAVA_REFRESH_TOKEN")
        
        if STRAVA_CLIENT_ID and STRAVA_REFRESH_TOKEN:
            try:
                from app.tools.strava_core import StravaTool
                self._strava_tool = StravaTool()
                logger.info("Strava tool initialized (Dependency)")
            except Exception as e:
                logger.error(f"Strava init failed: {e}")
        
        return self._strava_tool

    def get_code_executor(self):
        if self._code_executor:
            return self._code_executor

        if self._has_docker:
            try:
                from app.tools.code_executor import CodeExecutor
                self._code_executor = CodeExecutor()
                logger.info("CodeExecutor initialized (Dependency)")
            except Exception as e:
                logger.error(f"CodeExecutor init failed: {e}")
        
        return self._code_executor

# Singleton instance
_manager = DependencyManager()

# FastAPI Dependencies
def get_garmin():
    return _manager.get_garmin_tool()

def get_strava():
    return _manager.get_strava_tool()

def get_code_executor():
    return _manager.get_code_executor()
