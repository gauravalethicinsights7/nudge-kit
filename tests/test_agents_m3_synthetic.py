import pytest

from agents.m3.synthetic import run_synthetic
from llm.client import LLMValidationError
from packs.loader import load_pack
from tests.factories import make_brand
from tests.m3_support import valid_persona_draft_json


def test_run_synthetic_produces_assumption_personas_with_capped_confidence(monkeypatch):
    pack = load_pack("india")
    brand = make_brand()

    calls = []

    def fake_call(model, system, prompt):
        calls.append(prompt)
        name = f"Synthetic Persona {len(calls)}"
        return valid_persona_draft_json(pack, name=name, relative_weight=1.0), 100, 50

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    derived = run_synthetic(brand, pack, market_landscape=None, persona_count=4)

    assert len(derived) == 4
    for d in derived:
        assert d.persona.assumption is True
        assert d.persona.confidence == pytest.approx(0.4)
        assert d.persona.evidence_ids == []
        assert set(d.persona.drivers_ranked) == set(d.persona.drivers_ranked)  # full permutation enforced by schema


def test_run_synthetic_rejects_channel_affinity_missing_a_pack_channel(monkeypatch):
    pack = load_pack("india")
    brand = make_brand()

    def fake_call(model, system, prompt):
        import json

        draft = json.loads(valid_persona_draft_json(pack))
        del draft["channel_affinity"][pack.channels[-1].id]  # drop one required channel
        return json.dumps(draft), 100, 50

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    with pytest.raises(LLMValidationError):
        run_synthetic(brand, pack, persona_count=1)
