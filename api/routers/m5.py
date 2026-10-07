from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.m5.agent import run as run_m5_agent
from api.deps import get_brand, get_brand_pack, get_db, require_anthropic
from api.jobs import submit_job
from exporters.brand_plan import to_docx, to_markdown
from schemas.brand import Brand
from schemas.brand_plan import BrandPlan
from schemas.job import Job
from schemas.pack import Pack
from store.brand_plan_repo import BrandPlanRepo
from store.run_record_repo import RunRecordRepo

router = APIRouter(prefix="/brands/{brand_id}/m5", tags=["m5"])


class RunM5Request(BaseModel):
    net_price: float
    budget_envelope: float | None = None
    plan_horizon_months: int = 12
    require_approval: bool = True


@router.post("/run", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic)])
def run_m5(
    brand_id: UUID,
    body: RunM5Request,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    def _job_fn(session: Session) -> dict:
        result = run_m5_agent(
            brand, pack, session, net_price=body.net_price, budget_envelope=body.budget_envelope,
            plan_horizon_months=body.plan_horizon_months, require_approval=body.require_approval,
            run_record_repo=RunRecordRepo(session),
        )
        return {
            "key_issue_count": len(result.brand_plan.key_issues),
            "imperative_count": len(result.brand_plan.imperatives),
            "compliance_flag_count": len(result.brand_plan.compliance_flags),
            "review_checklist": result.review_checklist,
        }

    return submit_job(db, brand_id, "m5", _job_fn)


@router.get("/brand-plan", response_model=BrandPlan | None)
def get_brand_plan(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> BrandPlan | None:
    return BrandPlanRepo(db).get_latest_for_brand(brand_id)


@router.get("/brand-plan/export.md")
def export_brand_plan_markdown(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> Response:
    plan = BrandPlanRepo(db).get_latest_for_brand(brand_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="no brand plan found")
    return Response(content=to_markdown(plan), media_type="text/markdown")


@router.get("/brand-plan/export.docx")
def export_brand_plan_docx(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> FileResponse:
    plan = BrandPlanRepo(db).get_latest_for_brand(brand_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="no brand plan found")
    out_path = Path(tempfile.gettempdir()) / f"brand_plan_{brand_id}.docx"
    to_docx(plan, out_path)
    return FileResponse(
        out_path, filename="brand_plan.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
