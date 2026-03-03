import json
import logging
from typing import Any, Dict

from pydantic import BaseModel, Field

from app.services.scheduler_service import scheduler_service
from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ScheduleTaskSchema(BaseModel):
    instruction: str = Field(..., description="Instruction for Freja to perform (for example, 'Check server status').")
    cron: str = Field(..., description="Cron expression (for example, '0 8 * * *' for every day at 08:00).")


class ScheduleProcessSchema(BaseModel):
    process_name: str = Field(..., description="Registered process name to execute on schedule.")
    cron: str = Field(..., description="Cron expression (for example, '*/15 * * * *').")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Optional JSON payload passed to the process.")


class DeleteTaskSchema(BaseModel):
    job_id: str = Field(..., description="ID of the job to remove.")


class ListTasksSchema(BaseModel):
    pass


class ListProcessesSchema(BaseModel):
    pass


def schedule_task_impl(instruction: str, cron: str) -> str:
    """Schedule a new instruction-based task."""
    try:
        job_id = scheduler_service.add_task(instruction, cron)
        return f"Task '{instruction}' scheduled with ID: {job_id} (cron: {cron})"
    except Exception as exc:
        logger.error("Failed to schedule task: %s", exc)
        return f"Error scheduling task: {exc}"


def schedule_process_impl(process_name: str, cron: str, payload: Dict[str, Any]) -> str:
    """Schedule a process by name with optional JSON payload."""
    try:
        job_id = scheduler_service.add_process_task(process_name, cron, payload)
        serialized_payload = json.dumps(payload, ensure_ascii=False)
        return (
            f"Process '{process_name}' scheduled with ID: {job_id} "
            f"(cron: {cron}, payload: {serialized_payload})"
        )
    except Exception as exc:
        logger.error("Failed to schedule process '%s': %s", process_name, exc)
        return f"Error scheduling process: {exc}"


def list_tasks_impl() -> str:
    """List all scheduled tasks."""
    try:
        tasks = scheduler_service.list_tasks()
        if not tasks:
            return "No scheduled tasks found."

        output = "### Scheduled Tasks\n"
        for task in tasks:
            output += (
                f"- **ID**: `{task['id']}`\n"
                f"  **Task**: {task['name']}\n"
                f"  **Trigger**: {task['trigger']}\n"
                f"  **Next Run**: {task['next_run']}\n"
            )
        return output
    except Exception as exc:
        logger.error("Failed to list tasks: %s", exc)
        return f"Error listing tasks: {exc}"


def list_processes_impl() -> str:
    """List all registered scheduler process handlers."""
    try:
        processes = scheduler_service.list_registered_processes()
        if not processes:
            return "No registered scheduler processes found."
        process_rows = "\n".join(f"- `{name}`" for name in processes)
        return f"### Registered Scheduler Processes\n{process_rows}"
    except Exception as exc:
        logger.error("Failed to list registered processes: %s", exc)
        return f"Error listing registered processes: {exc}"


def delete_task_impl(job_id: str) -> str:
    """Delete a scheduled task."""
    try:
        scheduler_service.remove_task(job_id)
        return f"Task {job_id} deleted."
    except Exception as exc:
        logger.error("Failed to delete task: %s", exc)
        return f"Error deleting task: {exc}"


def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="schedule_autonomous_task",
        description="Schedule an instruction task for Freja using cron format.",
        args_schema=ScheduleTaskSchema,
    )(schedule_task_impl)

    registry.register(
        name="schedule_named_process",
        description="Schedule a named process with optional JSON payload.",
        args_schema=ScheduleProcessSchema,
    )(schedule_process_impl)

    registry.register(
        name="list_scheduled_tasks",
        description="List all scheduled autonomous tasks.",
        args_schema=ListTasksSchema,
    )(list_tasks_impl)

    registry.register(
        name="list_scheduler_processes",
        description="List all registered scheduler processes that can be scheduled.",
        args_schema=ListProcessesSchema,
    )(list_processes_impl)

    registry.register(
        name="delete_scheduled_task",
        description="Delete a scheduled task by ID.",
        args_schema=DeleteTaskSchema,
    )(delete_task_impl)
