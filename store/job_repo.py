from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.base import utcnow
from schemas.job import Job
from store.orm import JobORM


def _to_pydantic(row: JobORM) -> Job:
    return Job(
        id=row.id, brand_id=row.brand_id, module=row.module, status=row.status, message=row.message,
        result=row.result, error=row.error, created_at=row.created_at, updated_at=row.updated_at,
    )


class JobRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(self, brand_id: UUID, module: str) -> Job:
        job = Job(brand_id=brand_id, module=module)
        row = JobORM(
            id=job.id, brand_id=job.brand_id, module=job.module, status=job.status,
            created_at=job.created_at, updated_at=job.updated_at,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get(self, job_id: UUID) -> Job | None:
        row = self.session.get(JobORM, job_id)
        return _to_pydantic(row) if row else None

    def update_status(self, job_id: UUID, status: str, message: str | None = None, result: dict | None = None, error: str | None = None) -> None:
        row = self.session.get(JobORM, job_id)
        if row is None:
            return
        row.status = status
        row.updated_at = utcnow()
        if message is not None:
            row.message = message
        if result is not None:
            row.result = result
        if error is not None:
            row.error = error
        self.session.commit()

    def list_by_brand(self, brand_id: UUID, limit: int = 50) -> list[Job]:
        rows = self.session.scalars(
            select(JobORM).where(JobORM.brand_id == brand_id).order_by(JobORM.created_at.desc()).limit(limit)
        ).all()
        return [_to_pydantic(r) for r in rows]

    def reap_orphaned(self) -> int:
        """Called once at process startup. Any job still 'pending'/'running'
        belonged to a previous process's in-memory ThreadPoolExecutor (see
        api/jobs.py's own docstring: this is not a durable queue) — that
        pool no longer exists, so the job will never update again on its
        own. Mark it failed with an honest reason instead of leaving the UI
        polling a job that's actually dead. Returns the count reaped."""
        rows = self.session.scalars(select(JobORM).where(JobORM.status.in_(["pending", "running"]))).all()
        for row in rows:
            row.status = "failed"
            row.error = "interrupted by a server restart — this job system isn't a durable queue (see api/jobs.py); re-run it"
            row.updated_at = utcnow()
        if rows:
            self.session.commit()
        return len(rows)
