from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from llm.client import call
from models.evidence import confidence_score
from schemas.base import utcnow
from schemas.brand import Brand
from schemas.enums import EvidenceType, Origin, SourceCategory
from schemas.evidence import Evidence
from store.evidence_repo import EvidenceRepo
from tools.web import FetchedPage

PROMPTS_DIR = Path(__file__).parent / "prompts"


class ExtractedClaim(BaseModel):
    claim: str = Field(max_length=500)
    quote: str
    type: EvidenceType
    source_category: SourceCategory
    published_date: date | None = None
    entities_mentioned: list[str] = Field(default_factory=list)


class ExtractedClaims(BaseModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _quote_is_grounded(quote: str, page_text: str) -> bool:
    """Cheap, strong guardrail against a hallucinated quote: it must actually
    appear in the page. Per specs/m1-research.md 'never invent a number' — this
    generalises that to 'never invent a quote'."""
    return _normalize(quote) in _normalize(page_text)


def extract_evidence(
    page: FetchedPage,
    brand: Brand,
    evidence_repo: EvidenceRepo,
    *,
    run_record_repo=None,
) -> list[Evidence]:
    """Extracts atomic claims from one fetched page into persisted Evidence.
    Confidence is computed by models.evidence.confidence_score — the LLM only
    classifies category/date, never asserts a confidence number (CLAUDE.md
    rule 1). A claim whose quote isn't actually in the page is dropped, not
    trusted."""
    result = call(
        "extractor",
        {"url": page.url, "title": page.title, "page_text": page.text[:12000]},
        ExtractedClaims,
        model_tier="standard",
        module="m1_extractor",
        run_record_repo=run_record_repo,
        prompts_dir=PROMPTS_DIR,
    )

    publisher = urlparse(page.url).netloc
    today = utcnow().date()
    saved: list[Evidence] = []

    for extracted in result.claims:
        if not _quote_is_grounded(extracted.quote, page.text):
            continue

        confidence = confidence_score(extracted.source_category, extracted.published_date, today)
        evidence = Evidence(
            brand_id=brand.id,
            source=page.title or publisher,
            origin=Origin.external,
            as_of=today,
            confidence=confidence,
            type=extracted.type,
            claim=extracted.claim,
            quote=extracted.quote,
            source_url=page.url,
            publisher=publisher,
            published_date=extracted.published_date,
            entities_mentioned=extracted.entities_mentioned,
            source_category=extracted.source_category,
        )
        saved.append(evidence_repo.add(evidence))

    return saved
