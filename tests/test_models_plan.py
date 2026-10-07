from uuid import uuid4

from models.plan import build_review_checklist, check_compliance, rank_key_issues, revenue_at_stake
from packs.loader import load_pack
from schemas.enums import Tier
from schemas.hcp import Segment
from tests.factories import make_brand_plan


def _segment(total_potential: float, target_share: float, avg_share: float, name="Seg") -> Segment:
    return Segment(
        brand_id=uuid4(),
        name=name,
        rule={},
        tier=Tier.t1_grow,
        hcp_count=100,
        total_potential=total_potential,
        avg_share=avg_share,
        target_share=target_share,
    )


# ---- revenue_at_stake ----


def test_revenue_at_stake_zero_when_no_share_gap():
    segment = _segment(total_potential=1000, target_share=0.05, avg_share=0.10)
    result = revenue_at_stake(segment, net_price=100.0, currency="INR")
    assert result.value == 0.0
    assert result.currency == "INR"


def test_revenue_at_stake_positive_with_share_gap():
    segment = _segment(total_potential=1000, target_share=0.10, avg_share=0.02)
    result = revenue_at_stake(segment, net_price=100.0, currency="INR")
    assert result.value == (1000 * 0.08 * 100.0)


# ---- rank_key_issues ----


def test_rank_key_issues_orders_by_revenue_descending():
    low = _segment(total_potential=100, target_share=0.05, avg_share=0.04, name="Low")
    high = _segment(total_potential=10000, target_share=0.10, avg_share=0.01, name="High")
    ranked = rank_key_issues([low, high], net_price=50.0, currency="INR", top_n=6)
    assert [c.segment.name for c in ranked] == ["High", "Low"]


def test_rank_key_issues_never_pads_beyond_available_segments():
    ranked = rank_key_issues([_segment(100, 0.1, 0.01)], net_price=50.0, currency="INR", top_n=6)
    assert len(ranked) == 1


# ---- check_compliance ----


def test_check_compliance_flags_curated_trigger_phrase():
    pack = load_pack("india")
    plan = make_brand_plan()
    plan.message_house.core = "This therapy is completely safe with zero side effects for every patient."
    flags = check_compliance(plan, pack)
    assert any(f.rule_id == "IN-CLAIM-01" for f in flags)


def test_check_compliance_does_not_flag_ordinary_language():
    pack = load_pack("india")
    plan = make_brand_plan()
    plan.message_house.core = "Educational support helps professional prescribers manage titration."
    flags = check_compliance(plan, pack)
    assert flags == []


# ---- build_review_checklist ----


def test_build_review_checklist_covers_every_major_section():
    plan = make_brand_plan()
    checklist = build_review_checklist(plan)
    joined = " ".join(checklist)
    assert "situation" in joined.lower()
    assert any("key issue" in item.lower() for item in checklist)
    assert any("imperative" in item.lower() for item in checklist)
    assert any("positioning" in item.lower() for item in checklist)
    assert any("message pillar" in item.lower() for item in checklist)
