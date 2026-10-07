"""Step 1 (specs/m4-competitive.md): propose the competitor set from
MarketLandscape + Evidence context. Confirms top N by share (N <= 8) plus
recent entrants — since we don't have hard share numbers without the optional
share-audit CSV, "top by share" here is the LLM's qualitative read of the
gathered market evidence, bounded to <= 8 candidates by the schema itself.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from llm.client import call
from schemas.brand import Brand
from schemas.evidence import Evidence
from schemas.market_landscape import MarketLandscape

PROMPTS_DIR = Path(__file__).parent / "prompts"
MAX_COMPETITORS = 8  # spec: "confirm top N by share (N <= 8) + recent entrants"


class ProposedCompetitor(BaseModel):
    competitor_brand: str
    company: str


class CompetitorSetDraft(BaseModel):
    competitors: list[ProposedCompetitor] = Field(max_length=MAX_COMPETITORS)


def propose_competitor_set(
    brand: Brand,
    market_landscape: MarketLandscape | None,
    evidence: list[Evidence],
    *,
    run_record_repo=None,
) -> list[ProposedCompetitor]:
    landscape_summary = (
        json.dumps(market_landscape.model_dump(mode="json"), default=str)
        if market_landscape
        else "none available"
    )
    evidence_summary = "\n".join(f"[{e.type.value}] {e.claim}" for e in evidence[:100]) or "none available"

    result = call(
        "propose_competitor_set",
        {
            "brand_name": brand.name,
            "molecule": brand.molecule,
            "market": brand.market.value,
            "market_landscape_summary": landscape_summary,
            "evidence_summary": evidence_summary,
        },
        CompetitorSetDraft,
        model_tier="standard",
        module="m4_competitor_set",
        run_record_repo=run_record_repo,
        prompts_dir=PROMPTS_DIR,
    )
    return result.competitors
