from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_brand, get_db
from schemas.brand import Brand
from schemas.job import Job
from store.job_repo import JobRepo

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: UUID, db=Depends(get_db)) -> Job:
    # Deliberately not brand-scoped by path (a job's own brand_id is on the
    # row) — the frontend polls this straight off the job_id a run endpoint
    # just returned, which it could only have gotten by already passing that
    # brand's own auth check.
    job = JobRepo(db).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    return job


@router.get("/brands/{brand_id}/jobs", response_model=list[Job])
def list_jobs(brand_id: UUID, db=Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Job]:
    return JobRepo(db).list_by_brand(brand_id)
