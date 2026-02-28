import asyncio
import uuid
import time
import logging
from typing import Dict, Any, Optional
from enum import Enum
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class TaskResult:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status: TaskStatus = TaskStatus.QUEUED
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.step: str = "queued"
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None


class TaskQueue:
    """
    In-process async task queue for background alert processing.
    
    Features:
    - Surge protection with adaptive worker scaling
    - Task TTL and automatic cleanup of completed tasks
    - Metrics tracking (processed count, avg latency, failure count)
    
    Note: This is an in-memory queue suitable for single-instance deployments.
    For multi-instance production deployments, replace with Redis/Celery
    using the same interface (enqueue, get_status, get_all_tasks).
    Tasks are NOT persisted across restarts.
    """

    TASK_TTL_SECONDS = 3600
    CLEANUP_INTERVAL_SECONDS = 300
    SURGE_THRESHOLD = 0.8

    def __init__(self, max_workers: int = 5):
        self._tasks: Dict[str, TaskResult] = {}
        self._queue: asyncio.Queue = None
        self._base_max_workers = max_workers
        self._max_workers = max_workers
        self._active_worker_count = 0
        self._max_queue_size = settings.max_queue_size
        self._workers_started = False

        self._metrics = {
            "processed_count": 0,
            "failed_count": 0,
            "rejected_count": 0,
            "total_latency": 0.0,
        }

    async def _ensure_started(self):
        if not self._workers_started:
            self._queue = asyncio.Queue(maxsize=self._max_queue_size)
            for i in range(self._max_workers):
                asyncio.create_task(self._worker(i))
                self._active_worker_count += 1
            asyncio.create_task(self._cleanup_loop())
            self._workers_started = True
            logger.info(
                f"[QUEUE] Started {self._max_workers} workers. Max queue size: {self._max_queue_size}"
            )

    async def _worker(self, worker_id: int):
        while True:
            task_id, coro = await self._queue.get()
            task = self._tasks.get(task_id)
            if not task:
                self._queue.task_done()
                continue

            task.status = TaskStatus.PROCESSING
            start_time = time.time()
            try:
                result = await coro
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                latency = task.completed_at - task.created_at
                self._metrics["processed_count"] += 1
                self._metrics["total_latency"] += latency
                logger.info(f"[QUEUE] Worker-{worker_id} completed task {task_id} in {latency:.2f}s")
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()
                self._metrics["failed_count"] += 1
                logger.error(f"[QUEUE] Worker-{worker_id} failed task {task_id}: {e}")
            finally:
                self._queue.task_done()

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)
            self._cleanup_completed_tasks()
            await self._check_surge()

    def _cleanup_completed_tasks(self):
        now = time.time()
        expired = [
            tid for tid, task in self._tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.REJECTED)
            and task.completed_at
            and (now - task.completed_at) > self.TASK_TTL_SECONDS
        ]
        for tid in expired:
            del self._tasks[tid]
        if expired:
            logger.info(f"[QUEUE] Cleaned up {len(expired)} expired tasks")

    MAX_WORKER_CAP = 50

    async def _check_surge(self):
        if not self._queue:
            return
        utilization = self._queue.qsize() / max(self._max_queue_size, 1)
        if utilization >= self.SURGE_THRESHOLD and self._active_worker_count < self.MAX_WORKER_CAP:
            headroom = self.MAX_WORKER_CAP - self._active_worker_count
            additional = min(self._base_max_workers, 10, headroom)
            if additional <= 0:
                return
            for i in range(additional):
                worker_id = self._active_worker_count
                asyncio.create_task(self._worker(worker_id))
                self._active_worker_count += 1
            self._max_workers = self._active_worker_count
            logger.warning(
                f"[QUEUE] SURGE: Queue at {utilization:.0%} capacity. "
                f"Scaled to {self._max_workers} workers (+{additional}, cap {self.MAX_WORKER_CAP})"
            )

    async def enqueue(self, coro) -> str:
        await self._ensure_started()

        if self._queue.full():
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            task = TaskResult(task_id)
            task.status = TaskStatus.REJECTED
            task.error = "Queue is full. Try again later."
            task.completed_at = time.time()
            self._tasks[task_id] = task
            self._metrics["rejected_count"] += 1
            logger.warning(f"[QUEUE] REJECTED task {task_id}: queue full ({self._max_queue_size})")
            return task_id

        task_id = f"task-{uuid.uuid4().hex[:8]}"
        self._tasks[task_id] = TaskResult(task_id)
        await self._queue.put((task_id, coro))
        logger.info(f"[QUEUE] Enqueued {task_id}. Pending: {self._queue.qsize()}/{self._max_queue_size}")
        return task_id

    def get_status(self, task_id: str) -> Optional[TaskResult]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list:
        return [
            {"task_id": t.task_id, "status": t.status.value, "step": t.step}
            for t in self._tasks.values()
        ]

    def get_metrics(self) -> dict:
        processed = self._metrics["processed_count"]
        avg_latency = (
            self._metrics["total_latency"] / processed if processed > 0 else 0.0
        )
        return {
            "processed_count": processed,
            "failed_count": self._metrics["failed_count"],
            "rejected_count": self._metrics["rejected_count"],
            "avg_latency_seconds": round(avg_latency, 3),
            "active_workers": self._active_worker_count,
            "queue_depth": self._queue.qsize() if self._queue else 0,
            "max_queue_size": self._max_queue_size,
        }

    @property
    def pending_count(self) -> int:
        return self._queue.qsize() if self._queue else 0

    @property
    def worker_count(self) -> int:
        return self._active_worker_count


task_queue = TaskQueue()
