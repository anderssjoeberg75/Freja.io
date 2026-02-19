from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio
from typing import List, Dict, Any
from app.core import dependencies

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, db_url="sqlite:///jobs.sqlite"):
        self.jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        self.scheduler = AsyncIOScheduler(jobstores=self.jobstores)
        self.scheduler.start()
        logger.info("Scheduler Service started.")

    def add_task(self, instruction: str, cron_expression: str) -> str:
        """
        Schedules a task.
        Cron expression format: "minute hour day month day_of_week"
        (Standard cron formatting, but we can also parse simpler strings if needed)
        """
        # Parse cron string loosely or use standard format? 
        # For simplicity, let's assume '*/5 * * * *' format or keywords.
        # Actually APScheduler provides a robust trigger.
        
        # We need a function to execute.
        # It must be picklable or importable.
        # So we define a standalone function in this module or use a static method.
        
        job = self.scheduler.add_job(
            execute_scheduled_task,
            CronTrigger.from_crontab(cron_expression),
            args=[instruction],
            name=instruction
        )
        return job.id

    def list_tasks(self) -> List[Dict[str, Any]]:
        jobs = self.scheduler.get_jobs()
        return [{"id": j.id, "name": j.name, "next_run": str(j.next_run_time)} for j in jobs]

    def remove_task(self, job_id: str):
        self.scheduler.remove_job(job_id)

scheduler_service = SchedulerService()

async def execute_scheduled_task(instruction: str):
    """
    The function that actually runs when the timer fires.
    It needs to spawn a 'Chat' context effectively.
    """
    logger.info(f"Executing scheduled task: {instruction}")
    
    # We need to trigger the LLM to 'do' the task.
    # We can reuse the ChatService logic, but we need to verify dependencies aren't circular.
    try:
        # Import here to avoid circular imports during startup
        from app.services.chat_service import ChatService
        from app.core.config import settings
        # We need a dummy user_id or system id?
        
        # Ideally, we inject a "System Message" with the instruction.
        # "It is time to perform this scheduled task: {instruction}"
        
        # For now, let's just log it to prove it works.
        # Implementing full autonomous execution requires a user session or a "system" session.
        print(f"⏰ [SCHEDULER] Running: {instruction}")
        
        # REAL IMPLEMENTATION (Commented until ChatService is ready for headless mode)
        # chat_service = dependencies.get_chat_service() 
        # response = await chat_service.process_message(
        #    message=f"SYSTEM TRIGGER: Execute this scheduled task: {instruction}",
        #    model="gemini-2.0-flash", 
        #    user_id="system"
        # )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
