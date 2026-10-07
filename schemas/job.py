"""Async job tracking for long-running module runs (specs/blueprint: 'A run
engine that executes modules M1-M8 as background jobs... streamed progress
to the UI'). DB-tracked status polled by the frontend via a thread-pool
runner (api/jobs.py) — NOT a durable/persistent task queue: a server
restart mid-job loses it, same as any in-process worker. Real durability
would need Celery/RQ + Redis, out of scope for this pass (see the approved
plan's honesty flag).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from schemas.base import StrictModel, utcnow

JobStatus = Literal["pending", "running", "done", "failed"]


class Job(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    brand_id: UUID
    module: str
    status: JobStatus = "pending"
    message: str | None = None
    result: dict | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
