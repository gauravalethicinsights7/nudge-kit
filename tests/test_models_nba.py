from datetime import date

import pytest

from models.nba import (
    ActionCandidate,
    build_action_reason,
    p_respond,
    recency_decay,
    score_action,
    top_k_actions,
    value_gain,
)
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.enums import Access, Origin, PersonaDerivation, Rung, Setting
from schemas.hcp import HCP, Consent, ExternalIds, Geo
from schemas.persona import Persona


def _hcp(potential=1000.0) -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id="c1"),
        name_hash="h1",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(),
        potential=ProvNumber(value=potential, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        brand_share=ProvNumber(value=0.1, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        access=Access.open,
        consent=Consent(email=True, whatsapp=False),
    )


def _persona(affinity: dict[str, float]) -> Persona:
    from schemas.enums import Driver

    return Persona(
        brand_id=__import__("uuid").uuid4(),
        name="p",
        drivers_ranked=list(Driver),
        barriers_by_rung={Rung.aware: ["x"], Rung.considering: ["x"], Rung.trialist: ["x"]},
        channel_affinity=affinity,
        share_of_universe=0.5,
        share_of_potential=0.5,
        derivation=PersonaDerivation.synthetic,
        assumption=True,
    )


def test_recency_decay_is_one_when_no_touch_history():
    assert recency_decay(None) == 1.0


def test_recency_decay_rejects_negative_days():
    with pytest.raises(ValueError):
        recency_decay(-1.0)


def test_recency_decay_halves_at_half_life():
    assert recency_decay(14.0, half_life_days=14.0) == pytest.approx(0.5)


def test_recency_decay_is_monotonic_decreasing():
    values = [recency_decay(d) for d in [0, 7, 14, 30, 60]]
    assert values == sorted(values, reverse=True)


def test_p_respond_uses_channel_affinity_and_decay():
    persona = _persona({"rep_visit": 0.9})
    assert p_respond(persona, "rep_visit", days_since_last_touch=None) == pytest.approx(0.9)
    assert p_respond(persona, "rep_visit", days_since_last_touch=14.0) == pytest.approx(0.45)


def test_p_respond_defaults_to_neutral_affinity_when_channel_missing():
    persona = _persona({})
    assert p_respond(persona, "rep_visit") == pytest.approx(0.5)


def test_p_respond_defaults_to_neutral_when_no_persona():
    assert p_respond(None, "rep_visit") == pytest.approx(0.5)


def test_value_gain_is_positive_for_transitionable_rung():
    pack = load_pack("india")
    hcp = _hcp(potential=1200.0)
    v = value_gain(hcp, Rung.aware, pack)
    assert v > 0
    # pack.priors.rung_transition_monthly["aware"] * potential / 6 rung-steps
    expected = 1200.0 * pack.priors.rung_transition_monthly["aware"] / 6
    assert v == pytest.approx(expected)


def test_value_gain_is_zero_for_rung_with_no_pack_prior():
    pack = load_pack("india")
    hcp = _hcp()
    assert value_gain(hcp, Rung.advocate, pack) == 0.0  # neither pack defines advocate's transition prior


def test_score_action_formula():
    assert score_action(0.5, 100.0, 10.0) == pytest.approx(0.5 * 100.0 - 10.0)


def test_top_k_actions_orders_and_truncates():
    candidates = [
        ActionCandidate(channel_ref=f"c{i}", content_ref=None, score=float(i), p_respond_value=0.5, value_gain_value=1.0, cost=0.1)
        for i in range(5)
    ]
    top = top_k_actions(candidates, k=3)
    assert [c.channel_ref for c in top] == ["c4", "c3", "c2"]


def test_build_action_reason_is_nonempty_and_mentions_channel():
    candidate = ActionCandidate(
        channel_ref="rep_visit", content_ref="c1", score=1.5, p_respond_value=0.6, value_gain_value=10.0, cost=1.0
    )
    reason = build_action_reason(candidate)
    assert "rep_visit" in reason
