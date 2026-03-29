"""Tests for tidyforge.job_runner."""

from __future__ import annotations

from tidyforge.job_runner import Job, JobStatus, run_job


class TestJob:
    def test_initial_state(self) -> None:
        job = Job(name="test")
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert job.started_at is None

    def test_lifecycle(self) -> None:
        job = Job(name="test")
        job.mark_running("working...")
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

        job.mark_completed("done")
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 1.0
        assert job.finished_at is not None
        assert job.elapsed_seconds is not None

    def test_failure(self) -> None:
        job = Job(name="test")
        job.mark_running()
        job.mark_failed("something broke")
        assert job.status == JobStatus.FAILED
        assert job.error == "something broke"

    def test_elapsed_none_before_start(self) -> None:
        job = Job(name="test")
        assert job.elapsed_seconds is None


class TestRunJob:
    def test_success(self) -> None:
        def add(a: int, b: int) -> int:
            return a + b

        job, result = run_job("add", add, 2, 3)
        assert job.status == JobStatus.COMPLETED
        assert result == 5

    def test_failure(self) -> None:
        def fail() -> None:
            raise ValueError("oops")

        job, result = run_job("fail", fail)
        assert job.status == JobStatus.FAILED
        assert result is None
        assert "oops" in (job.error or "")
