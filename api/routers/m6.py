from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.m6.agent import run as run_m6_agent
from api.deps import get_brand, get_brand_pack, get_db
from api.jobs import submit_job
from schemas.brand import Brand
from schemas.channel import Channel
from schemas.channel_fit import ChannelFit
from schemas.channel_plan import ChannelPlan
from schemas.job import Job
from schemas.pack import Pack
from store.channel_fit_repo import ChannelFitRepo
from store.channel_plan_repo import ChannelPlanRepo
from store.channel_repo import ChannelRepo
from store.persona_repo import PersonaRepo
from store.segment_repo import SegmentRepo

router = APIRouter(prefix="/brands/{brand_id}/m6", tags=["m6"])


class RunM6Request(BaseModel):
    budget_envelope: float
    rep_count: int | None = None


@router.post("/run", status_code=202, response_model=Job)
def run_m6(
    brand_id: UUID,
    body: RunM6Request,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    segments = SegmentRepo(db).list_by_brand(brand_id)
    personas = PersonaRepo(db).list_by_brand(brand_id)
    if not segments:
        raise HTTPException(status_code=409, detail="no segments found — run M2 first")
    if not personas:
        raise HTTPException(status_code=409, detail="no personas found — run M3 first")

    def _job_fn(session: Session) -> dict:
        result = run_m6_agent(brand, pack, session, segments, personas, body.budget_envelope, rep_count=body.rep_count)
        return {
            "channel_count": len(result.channels),
            "channel_fit_count": len(result.channel_fits),
            "allocation_segment_count": len(result.channel_plan.allocations),
            "budget_line_count": len(result.budget_lines),
        }

    return submit_job(db, brand_id, "m6", _job_fn)


@router.get("/channels", response_model=list[Channel])
def list_channels(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Channel]:
    return ChannelRepo(db).list_by_brand(brand_id)


@router.get("/channel-fits", response_model=list[ChannelFit])
def list_channel_fits(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[ChannelFit]:
    return ChannelFitRepo(db).list_by_brand(brand_id)


@router.get("/channel-plan", response_model=ChannelPlan | None)
def get_channel_plan(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> ChannelPlan | None:
    return ChannelPlanRepo(db).get_latest_for_brand(brand_id)
