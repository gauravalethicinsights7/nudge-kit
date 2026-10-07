import json

from agents.m1.planner import plan_queries
from packs.loader import load_pack
from tests.factories import make_brand


def test_plan_queries_returns_llm_queries(monkeypatch):
    queries = [f"query {i}" for i in range(20)]

    def fake_call(model, system, prompt):
        return json.dumps({"queries": queries}), 100, 50

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    brand = make_brand()
    pack = load_pack(brand.market.value)

    result = plan_queries(brand, pack)

    assert result == queries
    assert len(result) == 20
