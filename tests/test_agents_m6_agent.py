import pytest

from agents.m6.agent import run as run_m6
from packs.loader import load_pack
from store.brand_plan_repo import BrandPlanRepo
from store.brand_repo import BrandRepo
from tests.factories import make_brand, make_brand_plan, make_persona, make_segment

pytestmark = pytest.mark.integration


def test_m6_run_builds_plan_and_fills_in_budget(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    draft_plan = BrandPlanRepo(db_session).add(make_brand_plan(brand.id))
    assert draft_plan.budget.placeholder is True  # M5's explicit placeholder, per CLAUDE.md

    pack = load_pack("india")
    segments = [make_segment(brand.id), make_segment(brand.id)]
    personas = [make_persona(brand.id)]

    result = run_m6(brand, pack, db_session, segments, personas, budget_envelope=100_000.0, rep_count=50)

    assert len(result.channels) == len(pack.channels)
    assert len(result.channel_fits) == len(segments) * len(pack.channels)
    assert set(result.channel_plan.allocations.keys()) == {s.id for s in segments}

    for by_channel in result.channel_plan.allocations.values():
        total_spend = sum(a.spend.value for a in by_channel.values())
        assert total_spend <= 100_000.0 + 1e-3

    updated_plan = BrandPlanRepo(db_session).get_latest_for_brand(brand.id)
    assert updated_plan.budget.placeholder is False
    assert len(updated_plan.budget.lines) > 0
    for line in updated_plan.budget.lines:
        assert line.position in {"under", "efficient", "saturated"}
        assert line.marginal_roi is not None


def test_m6_run_without_existing_brand_plan_still_builds_channel_plan(db_session):
    # no BrandPlanRepo.add() call first -> get_latest_for_brand returns None ->
    # agent must skip the update_budget call rather than crash
    brand = BrandRepo(db_session).add(make_brand())
    pack = load_pack("india")
    segments = [make_segment(brand.id)]
    personas = [make_persona(brand.id)]

    result = run_m6(brand, pack, db_session, segments, personas, budget_envelope=50_000.0)

    assert result.channel_plan is not None
    assert BrandPlanRepo(db_session).get_latest_for_brand(brand.id) is None
