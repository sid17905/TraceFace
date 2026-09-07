"""In-memory job manager for streaming multi-stage scan progress over SSE.

A *job* models one full provenance pipeline run (vision -> OSINT -> merkle seal
-> IPFS -> blockchain). Each stage transition is published as an event onto an
``asyncio.Queue`` that the SSE endpoint drains. State is kept purely in-process:
this is a single-worker demo/forensic tool, not a horizontally-scaled service.
If the API is ever run with multiple workers, this needs a shared broker (Redis
pub/sub) instead — that limitation is intentional and documented here.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Ordered pipeline stages surfaced to the UI radar / progress rail.
STAGES = (
    "face_extraction",
    "liveness_gate",
    "osint_crawl",
    "biometric_gate",
    "merkle_seal",
    "ipfs_pin",
    "blockchain_anchor",
)


@dataclass
class StageEvent:
    """A single progress event emitted while a job runs."""

    job_id: str
    stage: str
    status: str  # "started" | "progress" | "done" | "error" | "final"
    message: str = ""
    data: dict[str, Any] | None = None
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "stage": self.stage,
            "status": self.status,
            "message": self.message,
            "data": self.data,
            "ts": self.ts,
        }


@dataclass
class Job:
    job_id: str
    status: JobStatus = JobStatus.PENDING
    queue: asyncio.Queue[StageEvent | None] = field(default_factory=asyncio.Queue)
    events: list[StageEvent] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class JobManager:
    """Tracks running jobs and fans stage events out to SSE subscribers."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self) -> Job:
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        job = Job(job_id=job_id)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def publish(self, job: Job, event: StageEvent) -> None:
        """Record an event and hand it to any SSE subscriber."""

        job.events.append(event)
        await job.queue.put(event)

    async def close(self, job: Job) -> None:
        """Signal the SSE stream to complete by enqueuing a sentinel."""

        await job.queue.put(None)


# Process-wide singleton — the API runs single-worker (see module docstring).
job_manager = JobManager()
