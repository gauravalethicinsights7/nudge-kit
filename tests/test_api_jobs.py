"""api/jobs.py's thread-pool job runner — the one new synchronization-
sensitive piece this session (a worker thread opening its own DB session,
writing status transitions another request later reads)."""

import time

import pytest

from api.jobs import submit_job
from store.brand_repo import BrandRepo
from store.db import get_session
from store.job_repo import JobRepo
from tests.factories import make_brand

pytestmark = pytest.mark.integration


def _wait_for_terminal(job_id, timeout=5.0):
    session = get_session()
    try:
        repo = JobRepo(session)
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = repo.get(job_id)
            if job.status in ("done", "failed"):
                return job
            time.sleep(0.05)
        raise TimeoutError(f"job {job_id} never reached a terminal state")
    finally:
        session.close()


def test_submit_job_runs_and_records_success():
    db = get_session()
    try:
        brand_id = BrandRepo(db).add(make_brand()).id
        job = submit_job(db, brand_id, "test_module", lambda session: {"ok": True, "value": 42})
        assert job.status == "pending"
        finished = _wait_for_terminal(job.id)
        assert finished.status == "done"
        assert finished.result == {"ok": True, "value": 42}
        assert finished.error is None
    finally:
        db.close()


def test_submit_job_records_failure_without_crashing_the_pool():
    db = get_session()
    try:
        brand_id = BrandRepo(db).add(make_brand()).id

        def _boom(session):
            raise ValueError("deliberate failure for the test")

        job = submit_job(db, brand_id, "test_module", _boom)
        finished = _wait_for_terminal(job.id)
        assert finished.status == "failed"
        assert "deliberate failure" in finished.error
    finally:
        db.close()


def test_job_fn_receives_a_session_distinct_from_the_caller_s():
    """The whole point of the contract (api/jobs.py's docstring): fn gets a
    FRESH session, never the request-scoped one passed into submit_job."""
    db = get_session()
    try:
        brand_id = BrandRepo(db).add(make_brand()).id
        seen_session_ids = []

        def _job_fn(session):
            seen_session_ids.append(id(session))
            return {"done": True}

        job = submit_job(db, brand_id, "test_module", _job_fn)
        _wait_for_terminal(job.id)
        assert seen_session_ids[0] != id(db)
    finally:
        db.close()


def test_reap_orphaned_fails_jobs_stuck_from_a_previous_process():
    """Simulates what actually happens on a server restart mid-job: a job
    row stuck in 'running' with no live thread ever going to finish it.
    reap_orphaned (called at startup, api/main.py) must flip it to 'failed'
    with an explanatory error rather than leaving it polling forever."""
    db = get_session()
    try:
        repo = JobRepo(db)
        brand_id = BrandRepo(db).add(make_brand()).id
        stuck = repo.create(brand_id, "m4")
        repo.update_status(stuck.id, "running")
        done = repo.create(brand_id, "m2")
        repo.update_status(done.id, "done", result={"ok": True})

        reaped = repo.reap_orphaned()

        # This suite shares the real dev DB (see conftest.py) rather than
        # using transactional rollback, so other stray running/pending rows
        # may already exist — assert this test's own rows, not a global count.
        assert reaped >= 1
        stuck_after = repo.get(stuck.id)
        assert stuck_after.status == "failed"
        assert "server restart" in stuck_after.error
        done_after = repo.get(done.id)
        assert done_after.status == "done"  # untouched
    finally:
        db.close()
