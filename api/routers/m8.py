from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.m8 import agent as m8_agent
from api.deps import get_brand, get_brand_pack, get_db
from api.jobs import submit_job
from api.uploads_store import get_existing_upload
from exporters.scorecard import to_csv, to_markdown
from ingest.engagement_events_csv import load_engagement_events_csv
from ingest.hcp_csv import load_hcp_csv
from ingest.sales_csv import load_sales_csv
from models.pilot import match_pairs, required_sample_size
from schemas.brand import Brand
from schemas.enums import Rung
from schemas.job import Job
from schemas.measurement import AssumptionReview, LiftEstimate, Outcome, PriorUpdate, Scorecard
from schemas.pack import Pack
from store.adoption_state_repo import AdoptionStateRepo
from store.assumption_review_repo import AssumptionReviewRepo
from store.brand_plan_repo import BrandPlanRepo
from store.lift_estimate_repo import LiftEstimateRepo
from store.outcome_repo import OutcomeRepo
from store.prior_update_repo import PriorUpdateRepo
from store.scorecard_repo import ScorecardRepo

router = APIRouter(prefix="/brands/{brand_id}/m8", tags=["m8"])


class RunOutcomesRequest(BaseModel):
    period: str


@router.post("/run-outcomes", status_code=202, response_model=Job)
def run_outcomes(
    brand_id: UUID,
    body: RunOutcomesRequest,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> Job:
    brand_plan = BrandPlanRepo(db).get_latest_for_brand(brand_id)
    if brand_plan is None:
        raise HTTPException(status_code=409, detail="no brand plan found — run M5 first")

    hcp_path = get_existing_upload(brand_id, "hcp_sample")
    if hcp_path is None:
        raise HTTPException(status_code=409, detail="no HCP file uploaded — upload one in the Data Hub first")
    hcps = load_hcp_csv(hcp_path, pack)

    adoption_states = AdoptionStateRepo(db).list_by_brand(brand_id)

    events_path = get_existing_upload(brand_id, "engagement_events")
    engagement_events = load_engagement_events_csv(events_path, brand_id) if events_path else []

    sales_path = get_existing_upload(brand_id, "sales")
    sales_by_hcp_period = load_sales_csv(sales_path) if sales_path else {}

    channels_offered_by_hcp = {hcp.id: len(pack.channels) for hcp in hcps}

    def _job_fn(session: Session) -> dict:
        outcomes, scorecard = m8_agent.run_outcomes_and_scorecard(
            brand, pack, session, brand_plan, hcps, adoption_states, engagement_events,
            sales_by_hcp_period, channels_offered_by_hcp, body.period,
        )
        return {"outcome_count": len(outcomes), "scorecard_kpi_count": len(scorecard.kpis)}

    return submit_job(db, brand_id, "m8_outcomes", _job_fn)


@router.get("/outcomes", response_model=list[Outcome])
def list_outcomes(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[Outcome]:
    return OutcomeRepo(db).list_by_brand(brand_id)


@router.get("/scorecard", response_model=Scorecard | None)
def get_scorecard(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> Scorecard | None:
    return ScorecardRepo(db).get_latest_for_brand(brand_id)


@router.get("/scorecard/export.csv")
def export_scorecard_csv(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> Response:
    scorecard = ScorecardRepo(db).get_latest_for_brand(brand_id)
    if scorecard is None:
        raise HTTPException(status_code=404, detail="no scorecard found")
    return Response(content=to_csv(scorecard), media_type="text/csv")


@router.get("/scorecard/export.md")
def export_scorecard_markdown(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> Response:
    scorecard = ScorecardRepo(db).get_latest_for_brand(brand_id)
    if scorecard is None:
        raise HTTPException(status_code=404, detail="no scorecard found")
    return Response(content=to_markdown(scorecard), media_type="text/markdown")


class RunLiftTestRequest(BaseModel):
    test_name: str
    test_deltas: list[float]
    control_deltas: list[float]


@router.post("/lift-tests/did", response_model=LiftEstimate)
def run_lift_test(
    brand_id: UUID, body: RunLiftTestRequest, brand: Brand = Depends(get_brand), db: Session = Depends(get_db)
) -> LiftEstimate:
    return m8_agent.run_lift_test(brand, db, body.test_name, body.test_deltas, body.control_deltas)


class RunNationalLiftTestRequest(BaseModel):
    test_name: str
    pre_values: list[float]
    post_values: list[float]


@router.post("/lift-tests/national", response_model=LiftEstimate)
def run_national_lift_test(
    brand_id: UUID, body: RunNationalLiftTestRequest, brand: Brand = Depends(get_brand), db: Session = Depends(get_db)
) -> LiftEstimate:
    return m8_agent.run_national_lift_test(brand, db, body.test_name, body.pre_values, body.post_values)


@router.get("/lift-estimates", response_model=list[LiftEstimate])
def list_lift_estimates(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[LiftEstimate]:
    return LiftEstimateRepo(db).list_by_brand(brand_id)


class RunPriorUpdateRequest(BaseModel):
    rung: Rung
    successes: int
    trials: int
    period: str
    pseudo_count: float = 10.0


@router.post("/prior-updates", response_model=PriorUpdate)
def run_prior_update(
    brand_id: UUID,
    body: RunPriorUpdateRequest,
    brand: Brand = Depends(get_brand),
    pack: Pack = Depends(get_brand_pack),
    db: Session = Depends(get_db),
) -> PriorUpdate:
    return m8_agent.run_prior_update(brand, pack, db, body.rung, body.successes, body.trials, body.period, body.pseudo_count)


@router.get("/prior-updates", response_model=list[PriorUpdate])
def list_prior_updates(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[PriorUpdate]:
    return PriorUpdateRepo(db).list_by_brand(brand_id)


class RunAssumptionReviewRequest(BaseModel):
    period: str
    actual_values: dict[str, float]


@router.post("/assumption-reviews", response_model=AssumptionReview)
def run_assumption_review(
    brand_id: UUID, body: RunAssumptionReviewRequest, brand: Brand = Depends(get_brand), db: Session = Depends(get_db)
) -> AssumptionReview:
    brand_plan = BrandPlanRepo(db).get_latest_for_brand(brand_id)
    if brand_plan is None:
        raise HTTPException(status_code=409, detail="no brand plan found — run M5 first")
    return m8_agent.run_assumption_review(brand, db, brand_plan, body.actual_values, body.period)


@router.get("/assumption-reviews", response_model=list[AssumptionReview])
def list_assumption_reviews(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[AssumptionReview]:
    return AssumptionReviewRepo(db).list_by_brand(brand_id)


class PilotDesignRequest(BaseModel):
    effect_size: float
    std: float
    power: float = 0.8
    alpha: float = 0.05


@router.post("/pilot-design")
def pilot_design(
    brand_id: UUID, body: PilotDesignRequest, _brand: Brand = Depends(get_brand)
) -> dict:
    """models/pilot.py::required_sample_size — standard two-sample z-test
    sample-size formula, per spec's 'power calc for target effect.'"""
    try:
        n = required_sample_size(body.effect_size, body.std, body.power, body.alpha)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"required_sample_size_per_arm": n}


@router.post("/pilot-matching")
def pilot_matching(
    brand_id: UUID,
    db: Session = Depends(get_db),
    pack: Pack = Depends(get_brand_pack),
) -> list[dict]:
    """models/pilot.py::match_pairs over the brand's uploaded HCPs, matched
    by (potential, brand_share, rung-as-ordinal) — 'matched pairs by
    potential, share, rung mix' per spec. Needs an HCP upload + adoption
    states (run M2 first) to have a rung per HCP."""
    hcp_path = get_existing_upload(brand_id, "hcp_sample")
    if hcp_path is None:
        raise HTTPException(status_code=409, detail="no HCP file uploaded — upload one in the Data Hub first")
    hcps = load_hcp_csv(hcp_path, pack)
    rung_by_hcp = {a.hcp_id: a.rung for a in AdoptionStateRepo(db).list_by_brand(brand_id)}
    rung_order = list(Rung)

    def features(hcp) -> tuple[float, float, float]:
        rung = rung_by_hcp.get(hcp.id)
        rung_ordinal = float(rung_order.index(rung)) if rung is not None else 0.0
        return (hcp.potential.value, hcp.brand_share.value, rung_ordinal)

    pairs = match_pairs(hcps, features)
    return [
        {"hcp_a": p.a.external_ids.crm_id, "hcp_b": p.b.external_ids.crm_id, "distance": p.distance}
        for p in pairs[:50]
    ]
