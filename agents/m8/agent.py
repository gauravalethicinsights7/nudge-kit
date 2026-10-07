"""M8 orchestrator (specs/m8-measurement.md). Four independent entry points —
different input shapes, not one mega-function, same pattern as M3's
run_synthetic/run_survey/run_call_notes/run_social. Fully deterministic/
statistical, like M2/M6/M7 — no LLM calls anywhere in this module.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.lift import counterfactual_trend, diff_in_differences
from models.measurement import (
    DEFAULT_EI_WEIGHTS,
    compute_ei,
    compute_ei_components,
    review_assumptions,
    rung_transition_posterior,
)
from models.scorecard import build_kpi_results
from schemas.brand import Brand
from schemas.brand_plan import BrandPlan
from schemas.engagement import EngagementEvent
from schemas.enums import Rung
from schemas.hcp import HCP, AdoptionState
from schemas.measurement import AssumptionReview, LiftEstimate, Outcome, PriorUpdate, Scorecard
from schemas.pack import Pack
from store.assumption_review_repo import AssumptionReviewRepo
from store.lift_estimate_repo import LiftEstimateRepo
from store.outcome_repo import OutcomeRepo
from store.prior_update_repo import PriorUpdateRepo
from store.scorecard_repo import ScorecardRepo

DEFAULT_PERIOD_WEEKS = 4
DEFAULT_PSEUDO_COUNT = 10.0


def run_outcomes_and_scorecard(
    brand: Brand,
    pack: Pack,
    session: Session,
    brand_plan: BrandPlan,
    hcps: list[HCP],
    adoption_states: list[AdoptionState],
    engagement_events: list[EngagementEvent],
    sales_by_hcp_period: dict[tuple[str, str], tuple[float, float]],
    channels_offered_by_hcp: dict[UUID, int],
    period: str,
    ei_weights: dict[str, float] | None = None,
    period_weeks: int = DEFAULT_PERIOD_WEEKS,
) -> tuple[list[Outcome], Scorecard]:
    ei_weights = ei_weights or DEFAULT_EI_WEIGHTS
    rung_by_hcp = {a.hcp_id: a.rung for a in adoption_states}

    period_events = [e for e in engagement_events if e.period == period]
    events_by_hcp: dict[UUID, list[EngagementEvent]] = {}
    for event in period_events:
        events_by_hcp.setdefault(event.hcp_id, []).append(event)

    outcomes: list[Outcome] = []
    for hcp in hcps:
        channels_offered = channels_offered_by_hcp.get(hcp.id, 0)
        if channels_offered <= 0:
            continue  # can't compute a reach ratio with nothing offered — skip, don't fabricate

        components = compute_ei_components(events_by_hcp.get(hcp.id, []), channels_offered, period_weeks, pack)
        nrx, trx = sales_by_hcp_period.get((str(hcp.id), period), (None, None))
        outcomes.append(
            Outcome(
                brand_id=brand.id,
                hcp_id=hcp.id,
                period=period,
                engagement_index=compute_ei(components, ei_weights),
                rung=rung_by_hcp.get(hcp.id),
                nrx=nrx,
                trx=trx,
            )
        )
    saved_outcomes = OutcomeRepo(session).add_many(outcomes) if outcomes else []

    actuals: dict[str, float] = {}
    if saved_outcomes:
        actuals["engagement_index"] = sum(o.engagement_index for o in saved_outcomes) / len(saved_outcomes)
        nrx_values = [o.nrx for o in saved_outcomes if o.nrx is not None]
        if nrx_values:
            actuals["nrx"] = sum(nrx_values)
        trx_values = [o.trx for o in saved_outcomes if o.trx is not None]
        if trx_values:
            actuals["trx"] = sum(trx_values)
    if period_events and hcps:
        actuals["frequency"] = len(period_events) / len(hcps)
    if period_events:
        actuals["reach"] = len({e.channel for e in period_events}) / len(pack.channels)

    kpis = build_kpi_results(brand_plan.kpi_tree, actuals)
    scorecard = ScorecardRepo(session).add(Scorecard(brand_id=brand.id, period=period, kpis=kpis))

    return saved_outcomes, scorecard


def run_lift_test(brand: Brand, session: Session, test_name: str, test_deltas: list[float], control_deltas: list[float]) -> LiftEstimate:
    result = diff_in_differences(test_deltas, control_deltas)
    estimate = LiftEstimate(
        brand_id=brand.id, test_name=test_name, effect=result.effect, ci_low=result.ci_low, ci_high=result.ci_high, method=result.method
    )
    return LiftEstimateRepo(session).add(estimate)


def run_national_lift_test(brand: Brand, session: Session, test_name: str, pre_values: list[float], post_values: list[float]) -> LiftEstimate:
    result = counterfactual_trend(pre_values, post_values)
    estimate = LiftEstimate(
        brand_id=brand.id, test_name=test_name, effect=result.effect, ci_low=result.ci_low, ci_high=result.ci_high, method=result.method
    )
    return LiftEstimateRepo(session).add(estimate)


def run_prior_update(
    brand: Brand,
    pack: Pack,
    session: Session,
    rung: Rung,
    successes: int,
    trials: int,
    period: str,
    pseudo_count: float = DEFAULT_PSEUDO_COUNT,
) -> PriorUpdate:
    prior_p = pack.priors.rung_transition_monthly.get(rung.value, 0.0)
    _, _, posterior_mean = rung_transition_posterior(prior_p, pseudo_count, successes, trials)
    update = PriorUpdate(brand_id=brand.id, prior_type="rung_transition", key=rung.value, period=period, before=prior_p, after=posterior_mean)
    return PriorUpdateRepo(session).upsert(update)


def run_assumption_review(
    brand: Brand, session: Session, brand_plan: BrandPlan, actual_values: dict[str, float], period: str
) -> AssumptionReview:
    items = review_assumptions(brand_plan.forecast, actual_values)
    review = AssumptionReview(brand_id=brand.id, period=period, items=items)
    return AssumptionReviewRepo(session).add(review)
