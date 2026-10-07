import json
from datetime import date
from uuid import uuid4

import pytest

from agents.m5.sections import (
    build_imperatives,
    build_message_house,
    build_positioning,
    build_situation,
    word_key_issues,
)
from llm.client import LLMValidationError
from models.plan import KeyIssueCandidate
from schemas.base import ProvMoney
from schemas.competitive import MessageMap, Whitespace
from schemas.enums import Driver, Origin, Tier
from schemas.hcp import Segment
from tests.factories import make_brand, make_evidence, make_persona


def _segment() -> Segment:
    return Segment(
        brand_id=uuid4(), name="Seg", rule={}, tier=Tier.t1_grow, hcp_count=10,
        total_potential=100.0, avg_share=0.01, target_share=0.1,
    )


def _money(value=1000.0) -> ProvMoney:
    return ProvMoney(value=value, source="test", origin=Origin.estimated, as_of=date.today(), confidence=0.5, currency="INR")


def _fake_anthropic_returning(payload: dict):
    """A fake _call_anthropic that always returns the same JSON — used for the
    rejection tests, so the REAL llm.client.call retry-then-LLMValidationError
    logic runs (mocking call() itself would bypass that wrapper entirely and
    surface a raw pydantic.ValidationError instead)."""

    def fake(model, system, prompt):
        return json.dumps(payload), 10, 5

    return fake


def test_build_situation_accepts_valid_evidence(monkeypatch):
    brand = make_brand()
    evidence = make_evidence(brand.id)

    def fake_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate(
            {"summary": "A concise summary.", "key_facts": [{"text": "fact", "evidence_ids": [str(evidence.id)]}]},
            context=kwargs.get("validation_context"),
        )

    monkeypatch.setattr("agents.m5.sections.call", fake_call)
    situation = build_situation(brand, None, [evidence])
    assert situation.summary == "A concise summary."


def test_word_key_issues_rejects_wrong_count(monkeypatch):
    brand = make_brand()
    candidates = [KeyIssueCandidate(segment=_segment(), revenue_at_stake=_money())]

    monkeypatch.setattr("llm.client._call_anthropic", _fake_anthropic_returning({"issues": []}))
    with pytest.raises(LLMValidationError):
        word_key_issues(brand, candidates, [])


def test_word_key_issues_rejects_invented_evidence_id(monkeypatch):
    brand = make_brand()
    candidates = [KeyIssueCandidate(segment=_segment(), revenue_at_stake=_money())]

    monkeypatch.setattr(
        "llm.client._call_anthropic",
        _fake_anthropic_returning({"issues": [{"statement": "s", "barrier": "b", "evidence_ids": [str(uuid4())]}]}),
    )
    with pytest.raises(LLMValidationError):
        word_key_issues(brand, candidates, [])


def test_word_key_issues_accepts_valid_wording(monkeypatch):
    brand = make_brand()
    segment = _segment()
    candidates = [KeyIssueCandidate(segment=segment, revenue_at_stake=_money())]

    def fake_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate(
            {"issues": [{"statement": "Win T1 physicians", "barrier": "quality doubt", "evidence_ids": []}]},
            context=kwargs.get("validation_context"),
        )

    monkeypatch.setattr("agents.m5.sections.call", fake_call)
    result = word_key_issues(brand, candidates, [])
    assert len(result) == 1
    assert result[0].segment_id == segment.id
    assert result[0].revenue_at_stake is candidates[0].revenue_at_stake


def test_build_imperatives_rejects_unknown_key_issue_id(monkeypatch):
    brand = make_brand()

    monkeypatch.setattr(
        "llm.client._call_anthropic",
        _fake_anthropic_returning(
            {
                "imperatives": [
                    {"title": "t", "key_issue_ids": [str(uuid4())], "from_rung": "aware", "to_rung": "considering"}
                ]
            }
        ),
    )
    with pytest.raises(LLMValidationError):
        build_imperatives(brand, [])


def test_build_positioning_rejects_off_whitespace_driver(monkeypatch):
    brand = make_brand()
    message_map = MessageMap(
        brand_id=brand.id,
        whitespace=[Whitespace(driver=Driver.support_services, personas=[], rationale="r")],
    )

    monkeypatch.setattr(
        "llm.client._call_anthropic",
        _fake_anthropic_returning(
            {
                "target": "t",
                "frame_of_reference": "f",
                "point_of_difference": "p",
                "driver": "cost",  # not in whitespace
                "reasons_to_believe": [],
            }
        ),
    )
    with pytest.raises(LLMValidationError):
        build_positioning(brand, message_map, [])


def test_build_positioning_accepts_whitespace_driver(monkeypatch):
    brand = make_brand()
    message_map = MessageMap(
        brand_id=brand.id,
        whitespace=[Whitespace(driver=Driver.support_services, personas=[], rationale="r")],
    )

    def fake_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate(
            {
                "target": "t",
                "frame_of_reference": "f",
                "point_of_difference": "p",
                "driver": "support_services",
                "reasons_to_believe": [],
            },
            context=kwargs.get("validation_context"),
        )

    monkeypatch.setattr("agents.m5.sections.call", fake_call)
    positioning = build_positioning(brand, message_map, [])
    assert positioning.driver == Driver.support_services


def test_build_positioning_accepts_any_driver_when_message_map_has_no_whitespace(monkeypatch):
    """Regression test: a MessageMap that exists but found zero whitespace
    (M4 identified no uncontested driver — a legitimate, common outcome, not
    an error) must not block positioning entirely. The bug this guards
    against: build_positioning computed an empty *set* for this case instead
    of None, and the validator's `driver not in whitespace_drivers` check is
    vacuously true against an empty set — no driver could ever pass, so M5
    failed 100% of the time whenever M4 found no whitespace."""
    brand = make_brand()
    message_map = MessageMap(brand_id=brand.id, whitespace=[])

    def fake_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate(
            {
                "target": "t",
                "frame_of_reference": "f",
                "point_of_difference": "p",
                "driver": "cost",
                "reasons_to_believe": [],
            },
            context=kwargs.get("validation_context"),
        )

    monkeypatch.setattr("agents.m5.sections.call", fake_call)
    positioning = build_positioning(brand, message_map, [])
    assert positioning.driver == Driver.cost


def test_build_message_house_rejects_pillar_driver_not_in_any_persona_top3(monkeypatch):
    brand = make_brand()
    persona = make_persona()
    persona.drivers_ranked = [Driver.cost] + [d for d in Driver if d != Driver.cost]
    evidence = make_evidence(brand.id)  # top-3 for this ranking is [cost, efficacy, safety]

    monkeypatch.setattr(
        "llm.client._call_anthropic",
        _fake_anthropic_returning(
            {
                "core": "core",
                "pillars": [
                    {"driver": "support_services", "message": "m1", "proofs": [str(evidence.id)]},
                    {"driver": "cost", "message": "m2", "proofs": [str(evidence.id)]},
                    {"driver": "efficacy", "message": "m3", "proofs": [str(evidence.id)]},
                ],
                "by_persona": {},
            }
        ),
    )
    with pytest.raises(LLMValidationError):
        build_message_house(brand, [persona], [evidence])
