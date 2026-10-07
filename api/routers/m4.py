from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agents.m4.agent import run as run_m4_agent
from api.deps import get_brand, get_brand_pack, get_db, require_anthropic, require_serper
from api.jobs import submit_job
from schemas.brand import Brand
from schemas.competitive import Competitor, MessageMap
from schemas.early_warning_signal import EarlyWarningSignal
from schemas.job import Job
from schemas.pack import Pack
from store.competitor_repo import CompetitorRepo
from store.early_warning_signal_repo import EarlyWarningSignalRepo
from store.evidence_repo import EvidenceRepo
from store.market_landscape_repo import MarketLandscapeRepo
from store.message_map_repo import MessageMapRepo
from store.persona_repo import PersonaRepo
from store.run_record_repo import RunRecordRepo

router = APIRouter(prefix="/brands/{brand_id}/m4", tags=["m4"])


@router.post("/run", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic), Depends(require_serper)])
def run_m4(
    brand_id: UUID,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    market_landscape = MarketLandscapeRepo(db).get_latest_for_brand(brand_id)
    personas = PersonaRepo(db).list_by_brand(brand_id)
    evidence = EvidenceRepo(db).list_by_brand(brand_id)

    def _job_fn(session: Session) -> dict:
        result = run_m4_agent(
            brand, pack, session, market_landscape=market_landscape, personas=personas or None, evidence=evidence or None,
            run_record_repo=RunRecordRepo(session),
        )
        return {
            "competitor_count": len(result.competitors),
            "message_map_grid_size": len(result.message_map.grid),
            "early_warning_signal_count": len(result.early_warning_signals),
            "esov_skipped_reason": result.esov_skipped_reason,
        }

    return submit_job(db, brand_id, "m4", _job_fn)


@router.get("/competitors", response_model=list[Competitor])
def list_competitors(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Competitor]:
    return CompetitorRepo(db).list_by_brand(brand_id)


@router.get("/message-map", response_model=MessageMap | None)
def get_message_map(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> MessageMap | None:
    return MessageMapRepo(db).get_latest_for_brand(brand_id)


@router.get("/early-warning-signals", response_model=list[EarlyWarningSignal])
def list_early_warning_signals(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[EarlyWarningSignal]:
    return EarlyWarningSignalRepo(db).list_by_brand(brand_id)
