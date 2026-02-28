import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SCHEDULE_INTERVALS = {
    "every_1h": 3600,
    "every_6h": 21600,
    "every_12h": 43200,
    "daily": 86400,
    "weekly": 604800,
}


class CronJob:
    def __init__(self, job_id: str, name: str, schedule: str,
                 squad: str, task: str):
        self.id = job_id
        self.name = name
        self.schedule = schedule
        self.squad = squad
        self.task = task
        self.enabled = True
        self.last_run: Optional[str] = None
        self.next_run: Optional[str] = None
        interval = SCHEDULE_INTERVALS.get(schedule, 3600)
        self.next_run = (datetime.utcnow() + timedelta(seconds=interval)).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "task": self.task,
            "squad": self.squad,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
        }


class Scheduler:
    """
    Cyber Cron System: Security scheduler for recurring automated tasks.
    Users or the AI can set recurring tasks like periodic scans,
    defense updates, and compliance checks.
    """

    def __init__(self):
        self._jobs: Dict[str, CronJob] = {}
        self._running = False

    def add_job(self, job_id: str, name: str, schedule: str,
                squad: str, task: str) -> CronJob:
        job = CronJob(job_id, name, schedule, squad, task)
        self._jobs[job_id] = job
        logger.info(f"[SCHEDULER] Added job: {name} ({schedule})")
        return job

    def remove_job(self, job_id: str):
        if job_id in self._jobs:
            del self._jobs[job_id]

    def toggle_job(self, job_id: str) -> Optional[CronJob]:
        job = self._jobs.get(job_id)
        if job:
            job.enabled = not job.enabled
            return job
        return None

    def list_jobs(self) -> list:
        return [j.to_dict() for j in self._jobs.values()]

    async def start(self, agent_callback=None):
        """Start the background scheduler loop."""
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._loop(agent_callback))
        logger.info("[SCHEDULER] Background scheduler started")

    async def _loop(self, agent_callback=None):
        while self._running:
            now = datetime.utcnow()
            for job in self._jobs.values():
                if not job.enabled or not job.next_run:
                    continue
                try:
                    next_dt = datetime.fromisoformat(job.next_run)
                    if now >= next_dt:
                        logger.info(f"[SCHEDULER] Executing job: {job.name}")
                        job.last_run = now.isoformat()
                        interval = SCHEDULE_INTERVALS.get(job.schedule, 3600)
                        job.next_run = (now + timedelta(seconds=interval)).isoformat()

                        if agent_callback:
                            try:
                                await agent_callback(job.squad, job.task)
                            except Exception as e:
                                logger.error(f"[SCHEDULER] Job {job.name} failed: {e}")
                except Exception as e:
                    logger.error(f"[SCHEDULER] Error processing job {job.name}: {e}")

            await asyncio.sleep(60)


scheduler = Scheduler()
