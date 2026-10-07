import pytest

import agents.m4.agent as m4_agent
from schemas.base import utcnow
from schemas.enums import ClaimStrength, Driver
from store.brand_repo import BrandRepo
from tests.factories import make_brand
from tools.web import FetchedPage, SearchResult

pytestmark = pytest.mark.integration

PAGE_TEXT = (
    "Brand S is affordable for patients. "
    "CompetitorX lowered A1C significantly in trials. "
    "CompetitorX is also affordable for patients. "
    "A generic entrant received approval on 2026-01-15."
)


def _page(url: str) -> FetchedPage:
    return FetchedPage(url=url, title="t", text=PAGE_TEXT, fetched_at=utcnow())


def test_run_builds_grid_ews_and_persists(db_session, monkeypatch):
    brand = BrandRepo(db_session).add(make_brand())

    monkeypatch.setattr(
        "agents.m4.harvester.search",
        lambda query, count=3: [SearchResult(title="t", url="https://example.com/page", snippet="s")],
    )
    monkeypatch.setattr("agents.m4.harvester.fetch", _page)

    def fake_competitor_set_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate(
            {"competitors": [{"competitor_brand": "CompetitorX", "company": "Comp Co"}]}
        )

    def fake_harvester_call(prompt_id, variables, output_model, **kwargs):
        brand_name = variables["brand_name"]
        if prompt_id == "extract_competitor_claims":
            if brand_name == brand.name:
                claims = [{"quote": "Brand S is affordable for patients.", "driver": "cost", "source_category": "reputable_press"}]
            else:
                claims = [
                    {"quote": "CompetitorX lowered A1C significantly in trials.", "driver": "efficacy", "source_category": "reputable_press"},
                    {"quote": "CompetitorX is also affordable for patients.", "driver": "cost", "source_category": "reputable_press"},
                ]
            return output_model.model_validate({"claims": claims})
        if prompt_id == "extract_competitor_events":
            if brand_name == brand.name:
                return output_model.model_validate({"events": []})
            return output_model.model_validate(
                {
                    "events": [
                        {"type": "generic_entry", "date": "2026-01-15", "text": "A generic entrant received approval on 2026-01-15."}
                    ]
                }
            )
        raise AssertionError(prompt_id)

    def fake_ews_call(prompt_id, variables, output_model, **kwargs):
        import re

        cited_ids = re.findall(r"evidence_id=([0-9a-f-]{36})", variables["events_summary"])
        return output_model.model_validate(
            {
                "signals": [
                    {
                        "type": "generic_entry",
                        "detection_rule": "A new generic receives DCGI approval.",
                        "affected_segments": ["price-sensitive prescribers"],
                        "evidence_ids": cited_ids,
                    }
                ]
            },
            context=kwargs.get("validation_context"),
        )

    monkeypatch.setattr("agents.m4.competitor_set.call", fake_competitor_set_call)
    monkeypatch.setattr("agents.m4.harvester.call", fake_harvester_call)
    monkeypatch.setattr("agents.m4.agent.call", fake_ews_call)

    result = m4_agent.run(brand, pack=_pack(), session=db_session)

    grid_by_driver_brand = {(c.driver, c.brand): c.strength for c in result.message_map.grid}
    assert grid_by_driver_brand[(Driver.cost, brand.name)] == ClaimStrength.contested
    assert grid_by_driver_brand[(Driver.cost, "CompetitorX")] == ClaimStrength.contested
    assert grid_by_driver_brand[(Driver.efficacy, "CompetitorX")] == ClaimStrength.owned

    assert len(result.competitors) == 1
    assert result.competitors[0].competitor_brand == "CompetitorX"
    # the reconciled claim strength on the persisted Competitor matches the grid
    competitor_cost_claim = next(c for c in result.competitors[0].claims if c.driver == Driver.cost)
    assert competitor_cost_claim.strength == ClaimStrength.contested

    assert len(result.early_warning_signals) == 1
    assert result.early_warning_signals[0].type == "generic_entry"
    assert result.esov_skipped_reason == "no share audit / promo audit CSV provided"


def _pack():
    from packs.loader import load_pack

    return load_pack("india")
