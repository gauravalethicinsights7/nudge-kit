"""Steps 2-3 (specs/m4-competitive.md): per competitor (and our own brand, so
the grid genuinely covers 'drivers x brands incl. our brand'), fetch pages and
extract claims (tagged with Driver) and events. Reuses tools/web.py exactly
like agents/m1/retriever.py + extractor.py.

Claim *strength* (owned/contested/absent) isn't decided here — every claim is
built with a placeholder that agents/m4/agent.py overwrites once
models/competition.py::build_grid has seen all brands' claims together.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from llm.client import call
from models.evidence import confidence_score
from schemas.base import utcnow
from schemas.competitive import CompetitorClaim, CompetitorEvent
from schemas.early_warning_signal import EarlyWarningType
from schemas.enums import ClaimStrength, Driver, EvidenceType, Origin, SourceCategory
from schemas.evidence import Evidence
from store.evidence_repo import EvidenceRepo
from tools.web import FetchError, MissingAPIKeyError, fetch, search

PROMPTS_DIR = Path(__file__).parent / "prompts"
MAX_PAGES_PER_BRAND = 8  # bounds worst-case LLM calls, same rationale as M1's MAX_PAGES_PER_RUN


class ExtractedCompetitorClaim(BaseModel):
    quote: str
    driver: Driver
    source_category: SourceCategory
    published_date: date | None = None
    is_comparative: bool = False  # this brand's own material comparing itself to another brand


class ExtractedCompetitorClaims(BaseModel):
    claims: list[ExtractedCompetitorClaim] = Field(default_factory=list)


class ExtractedEvent(BaseModel):
    type: EarlyWarningType
    date: date
    text: str


class ExtractedEvents(BaseModel):
    events: list[ExtractedEvent] = Field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _retrieve_pages(brand_name: str, max_pages: int = MAX_PAGES_PER_BRAND) -> list:
    queries = [
        f"{brand_name} prescribing information label",
        f"{brand_name} efficacy safety clinical trial",
        f"{brand_name} price India",
        f"{brand_name} launch India",
    ]
    seen_urls: set[str] = set()
    pages = []
    for query in queries:
        if len(pages) >= max_pages:
            break
        try:
            results = search(query, count=3)
        except MissingAPIKeyError:
            raise
        except httpx.HTTPError:
            continue
        for result in results:
            if len(pages) >= max_pages:
                break
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            try:
                pages.append(fetch(result.url))
            except FetchError:
                continue
    return pages


def harvest_claims_and_events(
    brand_name: str,
    our_brand_id: UUID,
    evidence_repo: EvidenceRepo,
    *,
    run_record_repo=None,
) -> tuple[list[CompetitorClaim], list[CompetitorEvent]]:
    pages = _retrieve_pages(brand_name)
    today = utcnow().date()
    claims: list[CompetitorClaim] = []
    events: list[CompetitorEvent] = []

    for page in pages:
        publisher = urlparse(page.url).netloc

        claim_result = call(
            "extract_competitor_claims",
            {"brand_name": brand_name, "url": page.url, "page_text": page.text[:12000]},
            ExtractedCompetitorClaims,
            model_tier="standard",
            module="m4_harvest_claims",
            run_record_repo=run_record_repo,
            prompts_dir=PROMPTS_DIR,
        )
        for extracted in claim_result.claims:
            if _normalize(extracted.quote) not in _normalize(page.text):
                continue
            evidence = evidence_repo.add(
                Evidence(
                    brand_id=our_brand_id,
                    source=publisher,
                    origin=Origin.external,
                    as_of=today,
                    confidence=confidence_score(extracted.source_category, extracted.published_date, today),
                    type=EvidenceType.competitor_claim,
                    claim=extracted.quote[:500],
                    quote=extracted.quote,
                    source_url=page.url,
                    publisher=publisher,
                    published_date=extracted.published_date,
                    source_category=extracted.source_category,
                )
            )
            claims.append(
                CompetitorClaim(
                    driver=extracted.driver,
                    text=extracted.quote,
                    strength=ClaimStrength.absent,  # placeholder; agent.py fills in the real value
                    evidence_id=evidence.id,
                    requires_mlr_comparative=extracted.is_comparative,
                )
            )

        event_result = call(
            "extract_competitor_events",
            {
                "brand_name": brand_name,
                "url": page.url,
                "page_text": page.text[:12000],
                "as_of": today.isoformat(),
            },
            ExtractedEvents,
            model_tier="standard",
            module="m4_harvest_events",
            run_record_repo=run_record_repo,
            prompts_dir=PROMPTS_DIR,
        )
        for extracted in event_result.events:
            if _normalize(extracted.text) not in _normalize(page.text):
                continue
            evidence = evidence_repo.add(
                Evidence(
                    brand_id=our_brand_id,
                    source=publisher,
                    origin=Origin.external,
                    as_of=today,
                    confidence=confidence_score(SourceCategory.reputable_press, extracted.date, today),
                    type=EvidenceType.competitor_claim,
                    claim=extracted.text[:500],
                    quote=extracted.text,
                    source_url=page.url,
                    publisher=publisher,
                    published_date=extracted.date,
                )
            )
            events.append(
                CompetitorEvent(
                    date=extracted.date, type=extracted.type, text=extracted.text, evidence_id=evidence.id
                )
            )

    return claims, events
