from fastapi import APIRouter
from app.core import config
import logging
from app.core.dependencies import get_garmin, get_strava, get_code_executor
from app.services.tool_registry import registry
from skills._core.skill_loader import discover_and_register_skills

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/status")
async def get_status():
    """Returns system status including active agents"""
    
    agents = []
    known_agent_names = set()

    def add_agent(name: str, status: str, agent_type: str) -> None:
        if name in known_agent_names:
            return
        agents.append({"name": name, "status": status, "type": agent_type})
        known_agent_names.add(name)
    
    # Check Garmin (via Dependency)
    garmin_tool = get_garmin()
    if garmin_tool:
        add_agent("Garmin Coach", "Connected", "health")
    
    # Check Strava (via Dependency)
    strava_tool = get_strava()
    if strava_tool:
        add_agent("Strava Tracker", "Connected", "health")
    
    # Check Code Executor
    code_executor = get_code_executor()
    if code_executor:
        add_agent("Code Executor", "Active", "system")

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
            add_agent("Proactive Service", "Active", "automation")
        elif proactive_service:
            add_agent("Proactive Service", "Idle", "automation")
    except:
        pass

    for manifest in discover_and_register_skills(registry):
        skill_name = manifest.name.replace("_", " ").title()
        add_agent(skill_name, "Loaded", "skill")
    
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

@router.get("/api/system/backup_db")
async def backup_database():
    """Returns the current database file as a download."""
    from fastapi.responses import FileResponse
    from app.core.config import DB_PATH
    import os
    import datetime

    try:
        if not os.path.exists(DB_PATH):
            return {"error": "Database file not found"}

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mainframe_backup_{timestamp}.db"

        return FileResponse(
            path=DB_PATH,
            filename=filename,
            media_type='application/x-sqlite3'
        )
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return {"error": str(e)}

@router.get("/api/logs")
async def get_system_logs(limit: int = 100):
    """Returns the last N lines of the system log."""
    import os
    from app.core.config import BASE_DIR
    log_path = os.path.join(BASE_DIR, "logs", "daa.log")
    
    if not os.path.exists(log_path):
        return {"logs": []}
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Return last `limit` lines
            return {"logs": lines[-limit:]}
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return {"error": str(e), "logs": []}
