"""M5 orchestrator: reads approved-only upstream objects by default (CLAUDE.md
rule 8 — pass require_approval=False in dev before an approval UI exists),
ranks key issues, builds each LLM section, sizes objectives from the
deterministic forecast, checks compliance, persists the BrandPlan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from agents.m5.sections import (
    build_imperatives,
    build_message_house,
    build_positioning,
    build_situation,
    build_strategies_tactics,
    word_key_issues,
    word_objective_metrics,
)
from models.forecast import build_scenarios, compute_delta_nrx
from models.plan import build_review_checklist, check_compliance, rank_key_issues
from schemas.brand import Brand
from schemas.brand_plan import BrandPlan, KpiNode, KpiTree, Objective, RiskTest
from schemas.enums import Status
from schemas.hcp import Segment
from schemas.pack import Pack
from store.brand_plan_repo import BrandPlanRepo
from store.competitor_repo import CompetitorRepo
from store.evidence_repo import EvidenceRepo
from store.journey_map_repo import JourneyMapRepo
from store.market_landscape_repo import MarketLandscapeRepo
from store.message_map_repo import MessageMapRepo
from store.persona_repo import PersonaRepo
from store.segment_repo import SegmentRepo

RISK_TEST_COUNT = 3  # spec: "lowest-confidence assumptions"


@dataclass
class M5Result:
    brand_plan: BrandPlan
    review_checklist: list[str]


def _gather_upstream(session: Session, brand_id, require_approval: bool):
    status_filter = Status.approved if require_approval else None
    return (
        MarketLandscapeRepo(session).get_latest_for_brand(brand_id, status=status_filter),
        SegmentRepo(session).list_by_brand(brand_id, status=status_filter),
        PersonaRepo(session).list_by_brand(brand_id, status=status_filter),
        JourneyMapRepo(session).list_by_brand(brand_id, status=status_filter),
        CompetitorRepo(session).list_by_brand(brand_id, status=status_filter),
        MessageMapRepo(session).get_latest_for_brand(brand_id, status=status_filter),
    )


def _segment_for_imperative(imperative, segments_by_id, key_issues_by_id) -> Segment | None:
    if imperative.segment_id and imperative.segment_id in segments_by_id:
        return segments_by_id[imperative.segment_id]
    for key_issue_id in imperative.key_issue_ids:
        key_issue = key_issues_by_id.get(key_issue_id)
        if key_issue and key_issue.segment_id in segments_by_id:
            return segments_by_id[key_issue.segment_id]
    return None


def run(
    brand: Brand,
    pack: Pack,
    session: Session,
    net_price: float,
    budget_envelope: float | None = None,
    plan_horizon_months: int = 12,
    require_approval: bool = True,
    *,
    run_record_repo=None,
) -> M5Result:
    market_landscape, segments, personas, _journey_maps, _competitors, message_map = _gather_upstream(
        session, brand.id, require_approval
    )
    evidence = EvidenceRepo(session).list_by_brand(brand.id)

    situation = build_situation(brand, market_landscape, evidence, run_record_repo=run_record_repo)

    candidates = rank_key_issues(segments, net_price, pack.currency)
    key_issues = word_key_issues(brand, candidates, evidence, run_record_repo=run_record_repo)

    imperatives = build_imperatives(brand, key_issues, run_record_repo=run_record_repo)
    positioning = build_positioning(brand, message_map, evidence, run_record_repo=run_record_repo)
    message_house = build_message_house(brand, personas, evidence, run_record_repo=run_record_repo)

    segments_by_id = {s.id: s for s in segments}
    key_issues_by_id = {ki.id: ki for ki in key_issues}

    imperative_segment = {
        imperative.id: _segment_for_imperative(imperative, segments_by_id, key_issues_by_id)
        for imperative in imperatives
    }
    segments_and_from_rungs = [
        (segment, imperative.from_rung)
        for imperative in imperatives
        if (segment := imperative_segment[imperative.id]) is not None
    ]

    forecast = build_scenarios(
        segments_and_from_rungs, pack, net_price, pack.currency, budget_envelope, as_of=date.today()
    )

    metric_by_imperative = word_objective_metrics(brand, imperatives, run_record_repo=run_record_repo)
    due_date = date.today() + timedelta(days=30 * plan_horizon_months)

    objectives = []
    for imperative in imperatives:
        segment = imperative_segment[imperative.id]
        if segment is None:
            continue
        target = compute_delta_nrx(segment, imperative.from_rung, pack, persistence=1.0)
        objectives.append(
            Objective(
                imperative_id=imperative.id,
                metric=metric_by_imperative.get(imperative.id, "NRx"),
                baseline=0.0,
                target=target,
                due=due_date,
                segment_id=segment.id,
            )
        )

    strategies_tactics = build_strategies_tactics(
        brand, imperatives, message_house, run_record_repo=run_record_repo
    )

    kpi_tree = KpiTree(
        leading=[KpiNode(name=name) for name in pack.kpis.leading],
        lagging=[
            KpiNode(name=name, target=forecast.base.delta_nrx if "nrx" in name.lower() else None)
            for name in pack.kpis.lagging
        ],
    )

    plan = BrandPlan(
        brand_id=brand.id,
        plan_horizon_months=plan_horizon_months,
        situation=situation,
        key_issues=key_issues,
        imperatives=imperatives,
        positioning=positioning,
        message_house=message_house,
        objectives=objectives,
        strategies_tactics=strategies_tactics,
        kpi_tree=kpi_tree,
        forecast=forecast,
    )

    plan.compliance_flags = check_compliance(plan, pack)
    lowest_confidence = sorted(forecast.base.assumptions, key=lambda a: a.confidence)[:RISK_TEST_COUNT]
    plan.risks_tests = [
        RiskTest(
            assumption=a.name,
            confidence=a.confidence,
            test_design=f"Run a small pilot to validate the '{a.name}' assumption before scaling investment.",
            stop_go=f"Proceed if observed {a.name} is within 20% of the assumed value ({a.value:.2f}); otherwise revisit the plan.",
        )
        for a in lowest_confidence
    ]

    saved_plan = BrandPlanRepo(session).add(plan)
    return M5Result(brand_plan=saved_plan, review_checklist=build_review_checklist(saved_plan))
