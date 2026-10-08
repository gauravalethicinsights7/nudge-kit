"""Coverage for the question-bank read model (api/routers/m1.py).

The endpoint derives per-question status from the ResearchGap rows the agent
wrote, so the thing worth pinning is that the derivation matches gap_check's
own rule: no gap row means the question cleared the threshold, a
low_confidence row is partial, anything else is a gap. Getting that backwards
would overstate how well-researched a brand is — the exact claim the panel
exists to make checkable.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from agents.m1.planner import load_question_bank
from api.main import app
from schemas.research import ResearchGap
from store.research_gap_repo import ResearchGapRepo

pytestmark = pytest.mark.integration

client = TestClient(app)


def _auth() -> tuple[dict, str]:
    email = f"qb-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/auth/signup",
        json={"tenant_name": "QB Tenant", "name": "Admin", "email": email, "password": "a-decent-password"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    brand = client.post(
        "/brands",
        headers=headers,
        json={
            "name": f"QB Brand {uuid.uuid4().hex[:6]}",
            "molecule": "testmab",
            "indication": "testosis",
            "market": "india",
            "lifecycle_stage": "launch",
            "company": "QB Pharma",
        },
    )
    assert brand.status_code == 200, brand.text
    return headers, brand.json()["id"]


def test_reports_not_run_rather_than_28_findings_before_m1_runs():
    headers, brand_id = _auth()
    body = client.get(f"/brands/{brand_id}/m1/question-bank", headers=headers).json()

    bank = load_question_bank()
    assert body["has_run"] is False
    assert body["total"] == sum(len(q) for q in bank.values())
    assert body["answered"] == 0
    # Every question reads as a gap, but has_run=False is what lets the UI say
    # "not researched yet" instead of presenting these as real findings.
    assert body["gap"] == body["total"]


def test_status_per_question_follows_the_gap_rows(db_session):
    headers, brand_id = _auth()
    bank = load_question_bank()
    block, questions = next(iter(bank.items()))

    ResearchGapRepo(db_session).add_many(
        [
            ResearchGap(
                brand_id=uuid.UUID(brand_id),
                block=block,
                question=questions[0],
                best_confidence=0.0,
                reason="unanswered",
            ),
            ResearchGap(
                brand_id=uuid.UUID(brand_id),
                block=block,
                question=questions[1],
                best_confidence=0.31,
                reason="low_confidence",
            ),
        ]
    )
    db_session.commit()

    body = client.get(f"/brands/{brand_id}/m1/question-bank", headers=headers).json()
    assert body["has_run"] is True

    by_q = {
        q["question"]: q
        for b in body["blocks"]
        if b["block"] == block
        for q in b["questions"]
    }
    assert by_q[questions[0]]["status"] == "gap"
    assert by_q[questions[1]]["status"] == "partial"
    assert by_q[questions[1]]["best_confidence"] == pytest.approx(0.31)

    # A question with no gap row cleared the bar — not "unknown".
    untouched = [q for q in questions[2:]]
    for q in untouched:
        assert by_q[q]["status"] == "answered"
        assert by_q[q]["best_confidence"] is None

    assert body["gap"] == 1
    assert body["partial"] == 1
    assert body["answered"] == body["total"] - 2


def test_counts_sum_to_the_bank_size():
    headers, brand_id = _auth()
    body = client.get(f"/brands/{brand_id}/m1/question-bank", headers=headers).json()
    assert body["answered"] + body["partial"] + body["gap"] == body["total"]
