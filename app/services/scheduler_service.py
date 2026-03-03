from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

ProcessHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class SchedulerService:
    def __init__(self, db_url: str = "sqlite:///jobs.sqlite"):
        self.jobstores = {"default": SQLAlchemyJobStore(url=db_url)}
        self.scheduler = AsyncIOScheduler(jobstores=self.jobstores, timezone="UTC")
        self._process_handlers: Dict[str, ProcessHandler] = {}
        self.register_process("log_instruction", self._default_log_process)
        self.scheduler.start()
        logger.info("Scheduler service started")

    def register_process(self, process_name: str, handler: ProcessHandler) -> None:
        """Register a new process handler that can be scheduled by name."""
        normalized = process_name.strip().lower()
        if not normalized:
            raise ValueError("process_name must not be empty")
        self._process_handlers[normalized] = handler
        logger.info("Registered scheduler process '%s'", normalized)

    def list_registered_processes(self) -> List[str]:
        return sorted(self._process_handlers.keys())

    def add_task(self, instruction: str, cron_expression: str) -> str:
        """Schedule a standard instruction-based task."""
        instruction = instruction.strip()
        if not instruction:
            raise ValueError("instruction must not be empty")

        trigger = CronTrigger.from_crontab(cron_expression)
        job_id = f"instruction:{abs(hash((instruction, cron_expression)))}"
        job = self.scheduler.add_job(
            execute_scheduled_task,
            trigger,
            args=[instruction],
            id=job_id,
            name=instruction,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        return job.id

    def add_process_task(
        self,
        process_name: str,
        cron_expression: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Schedule a named process task with JSON payload."""
        normalized = process_name.strip().lower()
        if normalized not in self._process_handlers:
            raise ValueError(f"Unknown process: {process_name}")

        trigger = CronTrigger.from_crontab(cron_expression)
        serialized_payload = json.dumps(payload or {}, ensure_ascii=False)
        job_id = f"process:{normalized}:{abs(hash((normalized, cron_expression, serialized_payload)))}"
        job = self.scheduler.add_job(
            execute_named_process,
            trigger,
            args=[normalized, serialized_payload],
            id=job_id,
            name=f"process:{normalized}",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        return job.id

    def list_tasks(self) -> List[Dict[str, Any]]:
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]

    def remove_task(self, job_id: str) -> None:
        self.scheduler.remove_job(job_id)

    async def _default_log_process(self, payload: Dict[str, Any]) -> None:
        message = payload.get("message", "No payload message provided")
        logger.info("Scheduled process [log_instruction]: %s", message)


scheduler_service = SchedulerService()


async def execute_scheduled_task(instruction: str) -> None:
    """Execute a scheduled instruction task."""
    logger.info("Executing scheduled task: %s", instruction)
    try:
        print(f"⏰ [SCHEDULER] Running instruction: {instruction}")
    except Exception as exc:
        logger.error("Task execution failed: %s", exc)


async def execute_named_process(process_name: str, serialized_payload: str) -> None:
    """Execute a process previously registered in SchedulerService."""
    logger.info("Executing scheduled process: %s", process_name)
    try:
        payload = json.loads(serialized_payload) if serialized_payload else {}
        handler = scheduler_service._process_handlers[process_name]
        await handler(payload)
    except Exception as exc:
        logger.error("Scheduled process '%s' failed: %s", process_name, exc)
