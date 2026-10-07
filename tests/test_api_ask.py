"""Ask NUDGE (api/routers/ask.py) — no ANTHROPIC_API_KEY configured this
session, so this verifies the code path with llm.client.call mocked
(the require_anthropic gate itself is covered by tests/test_models... no —
by the fact every other LLM route already demonstrates the same 409 gate;
here we instead prove the context-digest + prompt-call wiring works once a
key *is* configured, via monkeypatch, matching the pattern used for M5's
sections in tests/test_agents_m5_sections.py).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def _signup_and_brand() -> tuple[dict, str]:
    email = f"ask-{uuid.uuid4().hex[:8]}@example.com"
    signup = client.post(
        "/auth/signup", json={"tenant_name": "Ask Tenant", "name": "A", "email": email, "password": "a-decent-password"}
    ).json()
    headers = {"Authorization": f"Bearer {signup['access_token']}"}
    brand = client.post(
        "/brands", headers=headers,
        json={"name": "Ask Brand", "molecule": "x", "indication": "y", "market": "india", "lifecycle_stage": "launch", "company": "C"},
    ).json()
    return brand, headers["Authorization"]


def test_ask_nudge_is_gated_without_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    brand, auth_header = _signup_and_brand()
    resp = client.post(f"/brands/{brand['id']}/ask", headers={"Authorization": auth_header}, json={"question": "What's our top segment?"})
    assert resp.status_code == 409


def test_ask_nudge_calls_the_llm_with_a_context_digest_when_configured(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-this-test")
    brand, auth_header = _signup_and_brand()

    captured = {}

    def fake_call(prompt_id, variables, output_model, **kwargs):
        captured["prompt_id"] = prompt_id
        captured["variables"] = variables
        return output_model.model_validate({"answer": "Your top segment is T1."})

    monkeypatch.setattr("api.routers.ask.call", fake_call)

    resp = client.post(f"/brands/{brand['id']}/ask", headers={"Authorization": auth_header}, json={"question": "What's our top segment?"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"answer": "Your top segment is T1."}
    assert captured["prompt_id"] == "ask_nudge"
    assert "Brand: Ask Brand" in captured["variables"]["context_digest"]
    assert captured["variables"]["question"] == "What's our top segment?"


def test_context_digest_reflects_missing_modules_honestly():
    from api.routers.ask import _context_digest
    from schemas.brand import Brand
    from schemas.enums import LifecycleStage, Market
    from store.db import get_session

    session = get_session()
    try:
        brand = Brand(
            name="Fresh Brand", molecule="m", indication="i", market=Market.india,
            lifecycle_stage=LifecycleStage.launch, company="c",
        )
        digest = _context_digest(session, brand)
        assert "M2 not run yet" in digest
        assert "M3 not run yet" in digest
        assert "M5 not run" in digest
        assert "M8 not run" in digest
    finally:
        session.close()
