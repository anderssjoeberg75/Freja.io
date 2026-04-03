import datetime
import os
import subprocess
import sys
import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import get_garmin, get_strava, get_code_executor
from app.core.security import require_admin
from skills._core.skill_loader import discover_skill_manifests

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_admin)])



class ScheduleInstructionRequest(BaseModel):
    instruction: str = Field(..., min_length=1, description="Instruction to run on schedule")
    cron: str = Field(..., min_length=9, description="Cron expression in crontab format")


class ScheduleProcessRequest(BaseModel):
    process_name: str = Field(..., min_length=1, description="Registered process name")
    cron: str = Field(..., min_length=9, description="Cron expression in crontab format")
    payload: dict = Field(default_factory=dict, description="Optional process payload")



@router.post("/api/self_update")
async def self_update(background_tasks: BackgroundTasks):
    """
    Uppdaterar Freja till senaste kod från GitHub och startar om tjänsten.
    """
    def do_update_and_restart():
        try:
            subprocess.run(["git", "pull"], check=True)
        except Exception as e:
            logger.error(f"Git pull misslyckades: {e}")
        # Starta om processen (systemd eller execv)
        if os.environ.get("FREJA_SYSTEMD", "0") == "1":
            subprocess.run(["systemctl", "restart", "freja.service"])
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)

    background_tasks.add_task(do_update_and_restart)
    return {"status": "Uppdatering påbörjad. Freja startar om sig själv."}


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

    try:
        from app.services.proactive_service import proactive_service
        if proactive_service and hasattr(proactive_service, 'running') and proactive_service.running:
            add_agent("Proactive Service", "Active", "automation")
        elif proactive_service:
            add_agent("Proactive Service", "Idle", "automation")
    except Exception:
        pass

    for manifest in discover_skill_manifests():
        skill_name = manifest.name.replace("_", " ").title()
        add_agent(skill_name, "Loaded", "skill")

    return {
        "system": "operational",
        "agents": agents
    }


@router.post("/api/integrations/garmin/reconnect")
async def reconnect_garmin():
    """Forces Garmin re-authentication by clearing tokens."""
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
            await proactive_service.trigger_briefing()
            return {"success": True, "message": "Morning briefing triggered"}
        else:
            return {"success": False, "message": "Proactive service not running"}
    except Exception as e:
        logger.error(f"Trigger error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/api/system/backup_db")
async def backup_database():
    """Returns a MySQL dump of the remote database as a download."""
    from fastapi.responses import FileResponse
    from app.core.database import _get_mysql_creds
    import subprocess
    import tempfile

    try:
        creds = _get_mysql_creds()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"freja_backup_{timestamp}.sql"
        tmp_file = os.path.join(tempfile.gettempdir(), filename)

        # We use SSH to run mysqldump on the remote host and pipe it back.
        # Since we have SSH root access, let's run it there and redirect to a local file.
        cmd = [
            "ssh", "root@db.andrix.local",
            f"mysqldump -u {creds['user']} -p'{creds['password']}' {creds['db']}"
        ]
        
        with open(tmp_file, "w") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown mysqldump error"
            logger.error(f"Backup failed: {error_msg}")
            return {"error": f"Backup failed: {error_msg}"}

        return FileResponse(
            path=tmp_file,
            filename=filename,
            media_type='application/sql'
        )
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return {"error": str(e)}


@router.get("/api/logs")
async def get_system_logs(limit: int = 100):
    """Returns the last N lines of the system log from journalctl."""
    import subprocess
    try:
        # Run journalctl to fetch the latest logs for freja.service
        # --no-pager avoids pausing output, -n limits the lines, --output=cat removes syslog prefixes
        result = subprocess.run(
            ["journalctl", "-u", "freja.service", "-n", str(limit), "--no-pager", "--output=cat"],
            capture_output=True,
            text=True,
            check=True
        )
        # Split into lines and remove trailing empty lines
        lines = result.stdout.strip().split("\n")
        logs = [line for line in lines if line]
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error reading journalctl logs: {e}")
        return {"error": str(e), "logs": []}



@router.get("/api/scheduler/processes")
async def list_scheduler_processes():
    """Return all scheduler process handlers that can be scheduled."""
    from app.services.scheduler_service import scheduler_service

    return {"processes": scheduler_service.list_registered_processes()}


@router.get("/api/scheduler/tasks")
async def list_scheduler_tasks():
    """Return all currently scheduled jobs."""
    from app.services.scheduler_service import scheduler_service

    return {"tasks": scheduler_service.list_tasks()}


@router.post("/api/scheduler/tasks/instruction")
async def create_instruction_task(body: ScheduleInstructionRequest):
    """Create or replace a scheduled instruction task."""
    from app.services.scheduler_service import scheduler_service

    job_id = scheduler_service.add_task(body.instruction, body.cron)
    return {"success": True, "job_id": job_id}


@router.post("/api/scheduler/tasks/process")
async def create_process_task(body: ScheduleProcessRequest):
    """Create or replace a scheduled named process."""
    from app.services.scheduler_service import scheduler_service

    job_id = scheduler_service.add_process_task(body.process_name, body.cron, body.payload)
    return {"success": True, "job_id": job_id}


@router.delete("/api/scheduler/tasks/{job_id}")
async def delete_scheduler_task(job_id: str):
    """Delete a scheduled job by ID."""
    from app.services.scheduler_service import scheduler_service

    scheduler_service.remove_task(job_id)
    return {"success": True, "job_id": job_id}


# ---------------------------------------------------------------------------
# Ollama Model Management
# ---------------------------------------------------------------------------

@router.get("/api/ollama/models")
async def list_ollama_models():
    """List all locally installed Ollama models."""
    import httpx
    from app.core.config import get_credential, settings as app_settings

    ollama_url = (get_credential("OLLAMA_URL") or app_settings.OLLAMA_URL).rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return {"models": data.get("models", [])}
    except Exception as e:
        logger.error(f"Ollama list error: {e}")
        return {"models": [], "error": str(e)}


@router.post("/api/ollama/pull")
async def pull_ollama_model(body: dict):
    """
    Pull (download/install) an Ollama model.
    Body: {"model": "llama3.2"}
    Returns streaming JSON lines from Ollama so the frontend can show progress.
    """
    import httpx
    from fastapi.responses import StreamingResponse
    from app.core.config import get_credential, settings as app_settings

    model = (body.get("model") or "").strip()
    if not model:
        return {"error": "model name required"}

    ollama_url = (get_credential("OLLAMA_URL") or app_settings.OLLAMA_URL).rstrip("/")

    async def stream_pull():
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                async with client.stream(
                    "POST",
                    f"{ollama_url}/api/pull",
                    json={"name": model, "stream": True},
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield line + "\n"
        except Exception as e:
            import json
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(stream_pull(), media_type="application/x-ndjson")


@router.delete("/api/ollama/models/{model_name:path}")
async def delete_ollama_model(model_name: str):
    """Delete a locally installed Ollama model."""
    import httpx
    from app.core.config import get_credential, settings as app_settings

    ollama_url = (get_credential("OLLAMA_URL") or app_settings.OLLAMA_URL).rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                "DELETE",
                f"{ollama_url}/api/delete",
                json={"name": model_name},
            )
            if resp.status_code in (200, 204):
                return {"success": True, "message": f"Deleted {model_name}"}
            return {"success": False, "error": resp.text}
    except Exception as e:
        logger.error(f"Ollama delete error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/api/ollama/ps")
async def ollama_ps():
    """Return currently running Ollama models and their memory usage."""
    import httpx
    from app.core.config import get_credential, settings as app_settings

    ollama_url = (get_credential("OLLAMA_URL") or app_settings.OLLAMA_URL).rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{ollama_url}/api/ps")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Ollama ps error: {e}")
        return {"models": [], "error": str(e)}


@router.get("/api/ollama/resources")
async def ollama_resources():
    """Return system memory and GPU info relevant to Ollama."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        ram = {
            "total_gb": round(vm.total / 1024 ** 3, 1),
            "used_gb": round(vm.used / 1024 ** 3, 1),
            "available_gb": round(vm.available / 1024 ** 3, 1),
            "percent": vm.percent,
        }
    except ImportError:
        ram = {"error": "psutil not installed"}
    except Exception as e:
        ram = {"error": str(e)}

    gpu = []
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    gpu.append({
                        "name": parts[0],
                        "vram_total_mb": int(parts[1]),
                        "vram_used_mb": int(parts[2]),
                        "vram_free_mb": int(parts[3]),
                        "utilization_pct": int(parts[4]),
                    })
    except Exception:
        pass  # No GPU or nvidia-smi not available

    return {"ram": ram, "gpu": gpu}


