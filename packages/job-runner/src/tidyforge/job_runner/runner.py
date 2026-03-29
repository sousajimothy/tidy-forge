"""Job lifecycle model and runner."""

from __future__ import annotations

import enum
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class JobStatus(enum.StrEnum):
    """Lifecycle states for a job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    """A trackable unit of work.

    Use ``mark_running()``, ``mark_completed()``, and ``mark_failed()``
    to transition state. Timestamps are set automatically.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def mark_running(self, message: str = "") -> None:
        """Transition to RUNNING state."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.message = message

    def mark_completed(self, message: str = "") -> None:
        """Transition to COMPLETED state."""
        self.status = JobStatus.COMPLETED
        self.progress = 1.0
        self.finished_at = datetime.now(UTC)
        self.message = message

    def mark_failed(self, error: str) -> None:
        """Transition to FAILED state."""
        self.status = JobStatus.FAILED
        self.finished_at = datetime.now(UTC)
        self.error = error

    @property
    def elapsed_seconds(self) -> float | None:
        """Seconds elapsed since the job started, or total duration if finished."""
        if self.started_at is None:
            return None
        end = self.finished_at or datetime.now(UTC)
        return (end - self.started_at).total_seconds()


def run_job(name: str, task: Callable[..., T], *args: Any, **kwargs: Any) -> tuple[Job, T | None]:
    """Run a callable as a tracked job.

    Args:
        name: Display name for the job.
        task: Callable to execute.
        *args: Positional arguments for the task.
        **kwargs: Keyword arguments for the task.

    Returns:
        Tuple of (Job, result). Result is None if the task raised an exception.
    """
    job = Job(name=name)
    job.mark_running(f"Starting {name}")

    try:
        result = task(*args, **kwargs)
        job.mark_completed(f"Finished {name}")
        return job, result
    except Exception as exc:
        job.mark_failed(str(exc))
        return job, None
