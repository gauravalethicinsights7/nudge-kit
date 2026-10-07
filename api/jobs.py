"""Async module-run tracking: a DB-persisted Job row + an in-process thread
pool. NOT a durable/persistent task queue (Celery/RQ + Redis) — a server
restart mid-job loses it, same as any in-process worker. What this buys is
the real UX win the blueprint actually cares about: a run doesn't block the
HTTP request, its status is visible and polled by the frontend, and it
leaves a run-history trail. True durability is a bigger, separate lift (new
service, new broker) — see the approved plan's honesty flag.

Contract: `fn` takes exactly one argument, a *fresh* SQLAlchemy Session (NOT
the request-scoped one from api/db_deps.py — that's closed the moment the
HTTP response is sent, long before the worker thread runs). Route handlers
build a closure over plain Pydantic values (Brand, Pack, parsed request
bodies, already-materialized lists) — never over the request's own `db` —
and `fn`'s body plugs the fresh session into the real agent call:

    def _job_fn(session):
        return run_m2_agent(brand, pack, hcps, body.target_share, session)
    job = submit_job(db, brand_id, "m2", _job_fn)
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from schemas.job import Job
from store.db import get_session
from store.job_repo import JobRepo

_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="nudge-job")


def _run_and_record(job_id: UUID, fn: Callable[[Session], Any]) -> None:
    session: Session = get_session()
    repo = JobRepo(session)
    try:
        repo.update_status(job_id, "running")
        result = fn(session)
        repo.update_status(job_id, "done", result=_to_jsonable(result))
    except Exception as e:  # the job's own failure, not a bug in the runner — record it, don't raise into the pool
        repo.update_status(job_id, "failed", error=str(e))
    finally:
        session.close()


def _to_jsonable(result: Any) -> dict:
    """Every route handler's job function returns a plain JSON-able summary
    dict already — this just guards against one that doesn't."""
    if isinstance(result, dict):
        return result
    return {"value": result}


def submit_job(db: Session, brand_id: UUID, module: str, fn: Callable[[Session], Any]) -> Job:
    job = JobRepo(db).create(brand_id, module)
    _EXECUTOR.submit(_run_and_record, job.id, fn)
    return job
