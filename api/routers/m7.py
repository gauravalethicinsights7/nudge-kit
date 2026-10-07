from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.m7.agent import run as run_m7_agent
from api.deps import get_brand, get_brand_pack, get_db
from api.jobs import submit_job
from api.uploads_store import get_existing_upload
from exporters.nba import to_csv, to_json
from ingest.content_library import load_content_library
from ingest.hcp_csv import load_hcp_csv
from schemas.brand import Brand
from schemas.content import ContentModule
from schemas.job import Job
from schemas.orchestration import Action, JourneyRule
from schemas.pack import Pack
from store.action_repo import ActionRepo
from store.adoption_state_repo import AdoptionStateRepo
from store.content_repo import ContentModuleRepo
from store.journey_map_repo import JourneyMapRepo
from store.journey_rule_repo import JourneyRuleRepo
from store.persona_assignment_repo import PersonaAssignmentRepo
from store.persona_repo import PersonaRepo
from store.segment_repo import SegmentRepo

router = APIRouter(prefix="/brands/{brand_id}/m7", tags=["m7"])


class RunM7Request(BaseModel):
    rep_count: int | None = None


@router.post("/run", status_code=202, response_model=Job)
def run_m7(
    brand_id: UUID,
    body: RunM7Request,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    segments = SegmentRepo(db).list_by_brand(brand_id)
    personas = PersonaRepo(db).list_by_brand(brand_id)
    adoption_states = AdoptionStateRepo(db).list_by_brand(brand_id)
    if not segments or not personas:
        raise HTTPException(status_code=409, detail="no segments/personas found — run M2 and M3 first")

    hcp_path = get_existing_upload(brand_id, "hcp_sample")
    hcps = load_hcp_csv(hcp_path, pack) if hcp_path else []

    content_path = get_existing_upload(brand_id, "content_library")
    if content_path is None:
        raise HTTPException(status_code=409, detail="no content library uploaded — upload one in the Data Hub first")
    content_library = load_content_library(content_path, brand_id)

    journey_maps = JourneyMapRepo(db).list_by_brand(brand_id)
    persona_assignments = PersonaAssignmentRepo(db).list_by_brand(brand_id)

    def _job_fn(session: Session) -> dict:
        result = run_m7_agent(
            brand, pack, session, segments, personas, hcps, adoption_states, content_library,
            journey_maps=journey_maps or None, persona_assignments=persona_assignments or None, rep_count=body.rep_count,
        )
        return {
            "channel_count": len(result.channels),
            "content_module_count": len(result.content_modules),
            "journey_rule_count": len(result.journey_rules),
            "action_count": len(result.actions),
            "content_briefs": [b.model_dump(mode="json") for b in result.content_briefs],
        }

    return submit_job(db, brand_id, "m7", _job_fn)


@router.get("/journey-rules", response_model=list[JourneyRule])
def list_journey_rules(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[JourneyRule]:
    return JourneyRuleRepo(db).list_by_brand(brand_id)


@router.get("/actions", response_model=list[Action])
def list_actions(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Action]:
    return ActionRepo(db).list_by_brand(brand_id)


@router.get("/content-modules", response_model=list[ContentModule])
def list_content_modules(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[ContentModule]:
    return ContentModuleRepo(db).list_by_brand(brand_id)


@router.get("/actions/export.csv")
def export_actions_csv(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> Response:
    actions = ActionRepo(db).list_by_brand(brand_id)
    return Response(content=to_csv(actions), media_type="text/csv")


@router.get("/actions/export.json")
def export_actions_json(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> Response:
    actions = ActionRepo(db).list_by_brand(brand_id)
    return Response(content=to_json(actions), media_type="application/json")
