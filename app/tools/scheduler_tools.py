from app.services.tool_registry import ToolRegistry
from pydantic import BaseModel, Field
from app.services.scheduler_service import scheduler_service
import logging

logger = logging.getLogger(__name__)

# --- Schemas ---

class ScheduleTaskSchema(BaseModel):
    instruction: str = Field(..., description="The instruction/task for Freja to perform (e.g., 'Check server status').")
    cron: str = Field(..., description="Cron expression for the schedule (e.g., '0 8 * * *' for daily at 08:00).")

class DeleteTaskSchema(BaseModel):
    job_id: str = Field(..., description="The ID of the job to remove.")

# --- Implementations ---

def schedule_task_impl(instruction: str, cron: str) -> str:
    """Schedules a new task for Freja to perform."""
    try:
        job_id = scheduler_service.add_task(instruction, cron)
        return f"Task '{instruction}' scheduled with ID: {job_id} (Cron: {cron})"
    except Exception as e:
        logger.error(f"Failed to schedule task: {e}")
        return f"Error scheduling task: {e}"

def list_tasks_impl() -> str:
    """Lists all scheduled tasks."""
    try:
        tasks = scheduler_service.list_tasks()
        if not tasks:
            return "No scheduled tasks found."
        
        output = "### Scheduled Tasks\n"
        for t in tasks:
            output += f"- **ID**: `{t['id']}`\n  **Task**: {t['name']}\n  **Next Run**: {t['next_run']}\n"
        return output
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return f"Error listing tasks: {e}"

def delete_task_impl(job_id: str) -> str:
    """Removes a scheduled task."""
    try:
        scheduler_service.remove_task(job_id)
        return f"Task {job_id} deleted."
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")
        return f"Error deleting task: {e}"

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="schedule_autonomous_task",
        description="Schedule a task for Freja to perform automatically at specific times. Use standard cron format.",
        args_schema=ScheduleTaskSchema,
    )(schedule_task_impl)

    registry.register(
        name="list_scheduled_tasks",
        description="List all currently scheduled autonomous tasks.",
        args_schema=BaseModel, # No args
    )(list_tasks_impl)
    
    registry.register(
        name="delete_scheduled_task",
        description="Delete a scheduled task by its ID.",
        args_schema=DeleteTaskSchema,
    )(delete_task_impl)
