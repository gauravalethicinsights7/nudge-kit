from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.m2.agent import run as run_m2_agent
from api.deps import get_brand, get_brand_pack, get_db
from api.jobs import submit_job
from api.uploads_store import get_existing_upload
from ingest.hcp_csv import load_hcp_csv
from schemas.brand import Brand
from schemas.hcp import AdoptionState, Segment
from schemas.job import Job
from schemas.pack import Pack
from schemas.target_list import TargetList
from store.adoption_state_repo import AdoptionStateRepo
from store.segment_repo import SegmentRepo
from store.target_list_repo import TargetListRepo

router = APIRouter(prefix="/brands/{brand_id}/m2", tags=["m2"])


class RunM2Request(BaseModel):
    target_share: float = 0.05


@router.post("/run", status_code=202, response_model=Job)
def run_m2(
    brand_id: UUID,
    body: RunM2Request,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    hcp_path = get_existing_upload(brand_id, "hcp_sample")
    hcps = load_hcp_csv(hcp_path, pack) if hcp_path else []

    def _job_fn(session: Session) -> dict:
        result = run_m2_agent(brand, pack, hcps, body.target_share, session)
        return {
            "mode": result.mode,
            "segment_count": len(result.segments),
            "adoption_state_count": len(result.adoption_states),
            "target_list_count": len(result.target_lists),
        }

    return submit_job(db, brand_id, "m2", _job_fn)


@router.get("/segments", response_model=list[Segment])
def list_segments(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Segment]:
    return SegmentRepo(db).list_by_brand(brand_id)


@router.get("/adoption-states", response_model=list[AdoptionState])
def list_adoption_states(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[AdoptionState]:
    return AdoptionStateRepo(db).list_by_brand(brand_id)


@router.get("/target-lists", response_model=list[TargetList])
def list_target_lists(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[TargetList]:
    return TargetListRepo(db).list_by_brand(brand_id)
