from datetime import date

import pytest

from agents.m8.agent import (
    run_assumption_review,
    run_lift_test,
    run_national_lift_test,
    run_outcomes_and_scorecard,
    run_prior_update,
)
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.engagement import EngagementEvent
from schemas.enums import Access, Origin, Rung, Setting
from schemas.hcp import HCP, AdoptionState, Consent, ExternalIds, Geo
from store.brand_repo import BrandRepo
from tests.factories import make_brand, make_brand_plan

pytestmark = pytest.mark.integration


def _hcp() -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id="c"),
        name_hash="h",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(),
        potential=ProvNumber(value=1000.0, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        brand_share=ProvNumber(value=0.1, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        access=Access.open,
        consent=Consent(email=True, whatsapp=True),
    )


def test_run_outcomes_and_scorecard_builds_both(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    pack = load_pack("india")
    brand_plan = make_brand_plan(brand.id)

    hcp_a, hcp_b = _hcp(), _hcp()
    hcps = [hcp_a, hcp_b]
    adoption_states = [
        AdoptionState(hcp_id=hcp_a.id, brand_id=brand.id, rung=Rung.aware, entered_on=date.today(), p_move_up=0.2),
        AdoptionState(hcp_id=hcp_b.id, brand_id=brand.id, rung=Rung.considering, entered_on=date.today(), p_move_up=0.1),
    ]
    engagement_events = [
        EngagementEvent(brand_id=brand.id, hcp_id=hcp_a.id, channel="rep_visit", depth="attended", occurred_at=date(2026, 1, 5), period="2026-01"),
        EngagementEvent(brand_id=brand.id, hcp_id=hcp_a.id, channel="whatsapp", depth="opened", occurred_at=date(2026, 1, 12), period="2026-01"),
    ]
    sales_by_hcp_period = {(str(hcp_a.id), "2026-01"): (2.0, 5.0)}
    channels_offered_by_hcp = {hcp_a.id: 4, hcp_b.id: 4}

    outcomes, scorecard = run_outcomes_and_scorecard(
        brand, pack, db_session, brand_plan, hcps, adoption_states, engagement_events,
        sales_by_hcp_period, channels_offered_by_hcp, period="2026-01",
    )

    assert len(outcomes) == 2
    outcome_a = next(o for o in outcomes if o.hcp_id == hcp_a.id)
    outcome_b = next(o for o in outcomes if o.hcp_id == hcp_b.id)
    assert 0.0 <= outcome_a.engagement_index <= 100.0
    assert outcome_a.engagement_index > outcome_b.engagement_index  # a engaged, b didn't
    assert outcome_a.nrx == 2.0
    assert outcome_b.nrx is None  # no sales row for b -> not fabricated

    assert scorecard.period == "2026-01"
    assert any(k.name == "nrx" for k in scorecard.kpis)


def test_run_outcomes_and_scorecard_skips_hcps_with_zero_channels_offered(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    pack = load_pack("india")
    brand_plan = make_brand_plan(brand.id)
    hcp = _hcp()

    outcomes, _ = run_outcomes_and_scorecard(
        brand, pack, db_session, brand_plan, [hcp], [], [], {}, channels_offered_by_hcp={}, period="2026-01",
    )
    assert outcomes == []


def test_run_lift_test_persists_a_did_estimate(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    estimate = run_lift_test(brand, db_session, "Metro pilot", test_deltas=[5.0, 6.0, 4.0], control_deltas=[1.0, 2.0, 0.5])
    assert estimate.method == "did"
    assert estimate.effect > 0


def test_run_national_lift_test_persists_a_counterfactual_estimate(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    pre = [10.0 + 0.5 * t for t in range(12)]
    post = [10.0 + 0.5 * (12 + t) + 3.0 for t in range(4)]
    estimate = run_national_lift_test(brand, db_session, "National launch", pre, post)
    assert estimate.method == "counterfactual_trend"
    assert estimate.effect == pytest.approx(3.0, abs=1.0)


def test_run_prior_update_is_idempotent_through_the_agent(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    pack = load_pack("india")
    first = run_prior_update(brand, pack, db_session, Rung.aware, successes=6, trials=20, period="2026-01")
    second = run_prior_update(brand, pack, db_session, Rung.aware, successes=6, trials=20, period="2026-01")
    assert first.id == second.id
    assert second.version == first.version + 1


def test_run_assumption_review_persists_checks(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    brand_plan = make_brand_plan(brand.id)
    review = run_assumption_review(brand, db_session, brand_plan, actual_values={"delta_nrx": 95.0}, period="2026-01")
    assert len(review.items) == 1
    assert review.items[0].assumption == "delta_nrx"
