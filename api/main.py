from __future__ import annotations

import os

from dotenv import load_dotenv

# Must run before importing api.routers: llm/config.py reads
# NUDGE_MODEL_TIER_*/NUDGE_RUN_BUDGET_USD at MODULE level (not lazily inside
# a function), and api.routers.m1/m3/m4/m5 transitively import it via their
# agent modules. Same ordering constraint evals/run.py documents, just
# stricter here since this file's own imports reach that module.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.routers import (  # noqa: E402
    approvals,
    ask,
    auth,
    brands,
    jobs,
    m1,
    m2,
    m3,
    m4,
    m5,
    m6,
    m7,
    m8,
    packs,
    run_records,
    system,
    uploads,
)

app = FastAPI(title="NUDGE Omnichannel API", version="0.1.0")


@app.on_event("startup")
def _reap_orphaned_jobs() -> None:
    """Any job left 'pending'/'running' from a previous process belonged to
    that process's in-memory thread pool, which is gone now — it will never
    complete on its own. Mark it failed on startup so the frontend doesn't
    poll a dead job forever. See store/job_repo.py::reap_orphaned."""
    from store.db import get_session
    from store.job_repo import JobRepo

    session = get_session()
    try:
        count = JobRepo(session).reap_orphaned()
        if count:
            print(f"[startup] reaped {count} orphaned job(s) from a previous process")
    finally:
        session.close()

_LOCAL_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
]
# Deployed frontends (Cloudflare Pages etc.) are added via CORS_ORIGINS, a
# comma-separated list, so the origin list isn't hard-coded per environment.
# CORS_ORIGIN_REGEX covers Pages' per-deploy preview URLs, which get a fresh
# hash subdomain on every push and so can't be enumerated ahead of time.
_env_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCAL_ORIGINS + _env_origins,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(uploads.router)
app.include_router(jobs.router)
app.include_router(ask.router)
app.include_router(m1.router)
app.include_router(m2.router)
app.include_router(m3.router)
app.include_router(m4.router)
app.include_router(m5.router)
app.include_router(m6.router)
app.include_router(m7.router)
app.include_router(m8.router)
app.include_router(approvals.router)
app.include_router(packs.router)
app.include_router(run_records.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
