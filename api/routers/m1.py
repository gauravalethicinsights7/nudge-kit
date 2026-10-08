from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agents.m1.agent import run as run_m1_agent
from agents.m1.gap_check import GAP_CONFIDENCE_THRESHOLD
from agents.m1.planner import load_question_bank
from api.deps import get_brand, get_brand_pack, get_db, require_anthropic, require_serper
from api.jobs import submit_job
from schemas.research import (
    QuestionBankCoverage,
    QuestionBlockCoverage,
    QuestionCoverage,
)
from schemas.brand import Brand
from schemas.evidence import Evidence
from schemas.job import Job
from schemas.market_landscape import MarketLandscape
from schemas.pack import Pack
from schemas.research import ResearchGap
from store.evidence_repo import EvidenceRepo
from store.market_landscape_repo import MarketLandscapeRepo
from store.research_gap_repo import ResearchGapRepo
from store.run_record_repo import RunRecordRepo

router = APIRouter(prefix="/brands/{brand_id}/m1", tags=["m1"])


@router.post("/run", status_code=202, response_model=Job, dependencies=[Depends(require_anthropic), Depends(require_serper)])
def run_m1(
    brand_id: UUID,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    def _job_fn(session: Session) -> dict:
        result = run_m1_agent(brand, pack, session, run_record_repo=RunRecordRepo(session))
        return {
            "has_market_landscape": result.market_landscape is not None,
            "evidence_count": len(result.evidence),
            "gap_count": len(result.gaps),
        }

    return submit_job(db, brand_id, "m1", _job_fn)


@router.get("/market-landscape", response_model=MarketLandscape | None)
def get_market_landscape(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> MarketLandscape | None:
    return MarketLandscapeRepo(db).get_latest_for_brand(brand_id)


@router.get("/evidence", response_model=list[Evidence])
def list_evidence(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Evidence]:
    return EvidenceRepo(db).list_by_brand(brand_id)


@router.get("/research-gaps", response_model=list[ResearchGap])
def list_research_gaps(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[ResearchGap]:
    return ResearchGapRepo(db).list_by_brand(brand_id)


@router.get("/question-bank", response_model=QuestionBankCoverage)
def get_question_bank_coverage(
    brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)
) -> QuestionBankCoverage:
    """Coverage of the fixed question bank for this brand.

    The bank is the same for every brand, which is the point: it's what makes
    "we researched this thoroughly" checkable instead of asserted. The status
    per question is derived from the gaps the agent recorded, using the same
    rule gap_check.py applied when it wrote them — a question with no gap row
    cleared the threshold.
    """
    bank = load_question_bank()
    gaps = {(g.block, g.question): g for g in ResearchGapRepo(db).list_by_brand(brand_id)}
    has_run = bool(gaps) or MarketLandscapeRepo(db).get_latest_for_brand(brand_id) is not None

    blocks: list[QuestionBlockCoverage] = []
    counts = {"answered": 0, "partial": 0, "gap": 0}

    for block, questions in bank.items():
        items: list[QuestionCoverage] = []
        for question in questions:
            gap = gaps.get((block, question))
            if not has_run:
                status = "gap"
                confidence = 0.0
            elif gap is None:
                status = "answered"
                confidence = None
            elif gap.reason == "low_confidence":
                status = "partial"
                confidence = gap.best_confidence
            else:
                status = "gap"
                confidence = gap.best_confidence
            if status in counts:
                counts[status] += 1
            items.append(
                QuestionCoverage(question=question, status=status, best_confidence=confidence)
            )
        blocks.append(QuestionBlockCoverage(block=block, questions=items))

    return QuestionBankCoverage(
        blocks=blocks,
        threshold=GAP_CONFIDENCE_THRESHOLD,
        total=sum(len(q) for q in bank.values()),
        answered=counts["answered"],
        partial=counts["partial"],
        gap=counts["gap"],
        has_run=has_run,
    )
