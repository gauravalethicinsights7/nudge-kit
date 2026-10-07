from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.m3.agent import run_call_notes as run_m3_call_notes_agent
from agents.m3.agent import run_social as run_m3_social_agent
from agents.m3.agent import run_survey as run_m3_survey_agent
from agents.m3.agent import run_synthetic as run_m3_synthetic_agent
from api.deps import get_brand, get_brand_pack, get_db, require_anthropic
from api.jobs import submit_job
from api.uploads_store import get_existing_upload
from ingest.call_notes_csv import load_call_notes_csv
from ingest.social_csv import load_social_csv
from ingest.survey_csv import load_survey_csv
from schemas.brand import Brand
from schemas.job import Job
from schemas.pack import Pack
from schemas.persona import JourneyMap, Persona
from store.journey_map_repo import JourneyMapRepo
from store.market_landscape_repo import MarketLandscapeRepo
from store.persona_assignment_repo import PersonaAssignmentRepo
from store.persona_repo import PersonaRepo
from store.run_record_repo import RunRecordRepo

router = APIRouter(prefix="/brands/{brand_id}/m3", tags=["m3"])


class RunM3SyntheticRequest(BaseModel):
    persona_count: int = 4


@router.post("/run-synthetic", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic)])
def run_m3_synthetic(
    brand_id: UUID,
    body: RunM3SyntheticRequest,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    market_landscape = MarketLandscapeRepo(db).get_latest_for_brand(brand_id)

    def _job_fn(session: Session) -> dict:
        result = run_m3_synthetic_agent(
            brand, pack, session, market_landscape=market_landscape, persona_count=body.persona_count,
            run_record_repo=RunRecordRepo(session),
        )
        return {
            "persona_count": len(result.personas),
            "journey_map_count": len(result.journey_maps),
            "distinctness_violations": result.distinctness_violations,
        }

    return submit_job(db, brand_id, "m3_synthetic", _job_fn)


@router.post("/run-call-notes", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic)])
def run_m3_call_notes(
    brand_id: UUID,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    notes_path = get_existing_upload(brand_id, "call_notes")
    if notes_path is None:
        raise HTTPException(status_code=409, detail="no call-notes file uploaded — upload one in the Data Hub first")
    notes = load_call_notes_csv(notes_path)

    def _job_fn(session: Session) -> dict:
        result = run_m3_call_notes_agent(brand, pack, notes, session, run_record_repo=RunRecordRepo(session))
        return {
            "persona_count": len(result.personas),
            "journey_map_count": len(result.journey_maps),
            "persona_assignment_count": len(result.persona_assignments),
        }

    return submit_job(db, brand_id, "m3_call_notes", _job_fn)


@router.post("/run-survey", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic)])
def run_m3_survey(
    brand_id: UUID,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    responses_path = get_existing_upload(brand_id, "survey_responses")
    if responses_path is None:
        raise HTTPException(status_code=409, detail="no survey-responses file uploaded — upload one in the Data Hub first")
    responses = load_survey_csv(responses_path)

    def _job_fn(session: Session) -> dict:
        result = run_m3_survey_agent(brand, pack, responses, session, run_record_repo=RunRecordRepo(session))
        return {"persona_count": len(result.personas), "journey_map_count": len(result.journey_maps)}

    return submit_job(db, brand_id, "m3_survey", _job_fn)


@router.post("/run-social", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic)])
def run_m3_social(
    brand_id: UUID,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    posts_path = get_existing_upload(brand_id, "social_posts")
    if posts_path is None:
        raise HTTPException(status_code=409, detail="no social-posts file uploaded — upload one in the Data Hub first")
    posts = load_social_csv(posts_path)

    def _job_fn(session: Session) -> dict:
        result = run_m3_social_agent(brand, pack, posts, session, run_record_repo=RunRecordRepo(session))
        return {
            "persona_count": len(result.personas),
            "journey_map_count": len(result.journey_maps),
            "persona_assignment_count": len(result.persona_assignments),
        }

    return submit_job(db, brand_id, "m3_social", _job_fn)


@router.get("/personas", response_model=list[Persona])
def list_personas(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Persona]:
    return PersonaRepo(db).list_by_brand(brand_id)


@router.get("/journey-maps", response_model=list[JourneyMap])
def list_journey_maps(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[JourneyMap]:
    return JourneyMapRepo(db).list_by_brand(brand_id)


@router.get("/persona-assignments")
def list_persona_assignments(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list:
    return PersonaAssignmentRepo(db).list_by_brand(brand_id)
