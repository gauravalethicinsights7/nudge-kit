import json

from agents.m1.extractor import extract_evidence
from schemas.base import utcnow
from tests.factories import make_brand
from tools.web import FetchedPage


class FakeEvidenceRepo:
    def __init__(self):
        self.added = []

    def add(self, evidence):
        self.added.append(evidence)
        return evidence


def _page():
    return FetchedPage(
        url="https://example.com/report",
        title="Some Report",
        text="India has about 101 million people with diabetes. Also some other text.",
        fetched_at=utcnow(),
    )


def test_extract_evidence_grounded_claim_is_kept(monkeypatch):
    def fake_call(model, system, prompt):
        return (
            json.dumps(
                {
                    "claims": [
                        {
                            "claim": "India has ~101M people with diabetes",
                            "quote": "India has about 101 million people with diabetes.",
                            "type": "epidemiology",
                            "source_category": "reputable_press",
                            "published_date": "2026-01-01",
                            "entities_mentioned": [],
                        }
                    ]
                }
            ),
            100,
            50,
        )

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    repo = FakeEvidenceRepo()
    brand = make_brand()
    result = extract_evidence(_page(), brand, repo)

    assert len(result) == 1
    assert len(repo.added) == 1
    assert result[0].confidence > 0  # computed deterministically, not asserted by the LLM
    assert result[0].brand_id == brand.id
    assert result[0].source_url == "https://example.com/report"


def test_extract_evidence_ungrounded_quote_is_dropped(monkeypatch):
    def fake_call(model, system, prompt):
        return (
            json.dumps(
                {
                    "claims": [
                        {
                            "claim": "A fabricated claim",
                            "quote": "This sentence does not appear anywhere on the page.",
                            "type": "market",
                            "source_category": "reputable_press",
                            "published_date": None,
                            "entities_mentioned": [],
                        }
                    ]
                }
            ),
            100,
            50,
        )

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    repo = FakeEvidenceRepo()
    result = extract_evidence(_page(), make_brand(), repo)

    assert result == []
    assert repo.added == []
