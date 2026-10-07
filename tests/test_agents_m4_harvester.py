import pytest

from agents.m4.harvester import harvest_claims_and_events
from schemas.base import utcnow
from schemas.enums import Driver
from store.brand_repo import BrandRepo
from store.evidence_repo import EvidenceRepo
from tests.factories import make_brand
from tools.web import FetchedPage, SearchResult

pytestmark = pytest.mark.integration


def test_harvest_claims_and_events_extracts_and_persists(db_session, monkeypatch):
    brand = BrandRepo(db_session).add(make_brand())

    page = FetchedPage(
        url="https://example.com/mounjaro",
        title="Mounjaro",
        text="Mounjaro lowered A1C significantly. Eli Lilly launched Mounjaro in India on March 20, 2025.",
        fetched_at=utcnow(),
    )

    monkeypatch.setattr(
        "agents.m4.harvester.search",
        lambda query, count=3: [SearchResult(title="t", url=page.url, snippet="s")],
    )
    monkeypatch.setattr("agents.m4.harvester.fetch", lambda url: page)

    def fake_call(prompt_id, variables, output_model, **kwargs):
        if prompt_id == "extract_competitor_claims":
            return output_model.model_validate(
                {
                    "claims": [
                        {
                            "quote": "Mounjaro lowered A1C significantly.",
                            "driver": "efficacy",
                            "source_category": "reputable_press",
                        }
                    ]
                }
            )
        if prompt_id == "extract_competitor_events":
            return output_model.model_validate(
                {
                    "events": [
                        {
                            "type": "launch",
                            "date": "2025-03-20",
                            "text": "Eli Lilly launched Mounjaro in India on March 20, 2025.",
                        }
                    ]
                }
            )
        raise AssertionError(f"unexpected prompt_id {prompt_id}")

    monkeypatch.setattr("agents.m4.harvester.call", fake_call)

    claims, events = harvest_claims_and_events("Mounjaro", brand.id, EvidenceRepo(db_session))

    assert len(claims) == 1
    assert claims[0].driver == Driver.efficacy
    assert claims[0].requires_mlr_comparative is False
    assert len(events) == 1
    assert events[0].type == "launch"


def test_harvest_drops_ungrounded_claims_and_events(db_session, monkeypatch):
    brand = BrandRepo(db_session).add(make_brand())
    page = FetchedPage(
        url="https://example.com/mounjaro",
        title="Mounjaro",
        text="Mounjaro lowered A1C significantly.",
        fetched_at=utcnow(),
    )

    monkeypatch.setattr(
        "agents.m4.harvester.search",
        lambda query, count=3: [SearchResult(title="t", url=page.url, snippet="s")],
    )
    monkeypatch.setattr("agents.m4.harvester.fetch", lambda url: page)

    def fake_call(prompt_id, variables, output_model, **kwargs):
        if prompt_id == "extract_competitor_claims":
            return output_model.model_validate(
                {
                    "claims": [
                        {
                            "quote": "This sentence never appeared on the page.",
                            "driver": "efficacy",
                            "source_category": "reputable_press",
                        }
                    ]
                }
            )
        return output_model.model_validate({"events": []})

    monkeypatch.setattr("agents.m4.harvester.call", fake_call)

    claims, events = harvest_claims_and_events("Mounjaro", brand.id, EvidenceRepo(db_session))

    assert claims == []
    assert events == []
