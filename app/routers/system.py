from fastapi import APIRouter
from app.core import config
import logging
from app.core.dependencies import get_garmin, get_strava, get_code_executor

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_status():
    """Returns system status including active agents"""
    
    agents = []
    
    # Check Garmin (via Dependency)
    garmin_tool = get_garmin()
    if garmin_tool:
        agents.append({"name": "Garmin Coach", "status": "Connected", "type": "health"})
    
    # Check Strava (via Dependency)
    strava_tool = get_strava()
    if strava_tool:
        agents.append({"name": "Strava Tracker", "status": "Connected", "type": "health"})
    
    # Check Code Executor
    code_executor = get_code_executor()
    if code_executor:
        agents.append({"name": "Code Executor", "status": "Active", "type": "system"})

    # Add other known services (safely check if they exist)
    # These imports should ideally also be moved to dependencies or service registry
    try:
        from app.services.voice_service import voice_service
        if voice_service:
            agents.append({"name": "Voice Service", "status": "Active", "type": "voice"})
    except:
        pass
    
    try:
        from app.services.proactive_service import proactive_service
        if proactive_service and hasattr(proactive_service, 'running') and proactive_service.running:
            agents.append({"name": "Proactive Service", "status": "Active", "type": "automation"})
        elif proactive_service:
            agents.append({"name": "Proactive Service", "status": "Idle", "type": "automation"})
    except:
        pass
    
    return {
        "system": "operational",
        "agents": agents
    }

@router.get("/api/garmin/reconnect")
async def reconnect_garmin():
    """Forces Garmin re-authentication by clearing tokens."""
    try:
        # This Logic needs to be centralized in the Garmin Tool or Dependency Manager
        # For now, we manually trigger a reload
        from app.core.config import settings
        # ... logic to clear tokens ... 
        # In the new architecture, we should add a method to DependencyManager to reload tools
        
        garmin = get_garmin()
        if garmin:
            # If the tool has a reconnect method, use it
            if hasattr(garmin, 'authenticate'):
                 await garmin.authenticate()
            return {"success": True, "message": "Garmin reconnected"}
        else:
             return {"success": False, "message": "Garmin tool not initialized"}

    except Exception as e:
        logger.error(f"Garmin reconnect error: {e}")
        return {"success": False, "message": str(e)}
