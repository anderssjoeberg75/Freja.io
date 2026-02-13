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
    # Voice Service removed
    # try:
    #     from app.services.voice_service import voice_service
    #     if voice_service:
    #         agents.append({"name": "Voice Service", "status": "Active", "type": "voice"})
    # except:
    #     pass
    
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

@router.post("/api/integrations/garmin/reconnect")
async def reconnect_garmin():
    """Forces Garmin re-authentication by clearing tokens."""
    import os
    import shutil
    
    try:
        # Clear cached tokens
        token_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "garmin_tokens")
        if os.path.exists(token_dir):
            shutil.rmtree(token_dir)
            logger.info(f"Cleared Garmin tokens from {token_dir}")
        
        # Reset the cached garmin tool in DependencyManager
        from app.core.dependencies import _manager
        _manager._garmin_tool = None
        
        # Re-initialize
        garmin = get_garmin()
        if garmin and garmin.client:
            return {"success": True, "message": "Garmin reconnected successfully!"}
        else:
            return {"success": False, "message": "Garmin login failed - check credentials or try logging in at connect.garmin.com first"}

    except Exception as e:
        logger.error(f"Garmin reconnect error: {e}")
        return {"success": False, "message": str(e)}

@router.post("/api/proactive/trigger-morning-briefing")
async def trigger_morning_briefing():
    """Manually triggers the morning briefing (for testing)."""
    try:
        from app.services.proactive_service import proactive_service
        if proactive_service:
            # Run in background or await? Await to see errors
            await proactive_service.trigger_briefing()
            return {"success": True, "message": "Morning briefing triggered"}
        else:
            return {"success": False, "message": "Proactive service not running"}
    except Exception as e:
        logger.error(f"Trigger error: {e}")
        return {"success": False, "message": str(e)}
