"""Deterministic confidence heuristic for M1 (specs/m1-research.md).

Per CLAUDE.md rule 1 ("the LLM never does arithmetic"), the extractor LLM only
classifies a claim's SourceCategory and reads its published_date — this
function is the actual scoring math, and it's a pure function so it's fully
unit-testable without touching the LLM.
"""

from datetime import date

from schemas.enums import SourceCategory

BASE_CONFIDENCE: dict[SourceCategory, float] = {
    SourceCategory.peer_reviewed_guideline_regulator: 0.9,
    SourceCategory.audit_market_vendor: 0.8,
    SourceCategory.reputable_press: 0.6,
    SourceCategory.vendor_blog: 0.4,
    SourceCategory.forum: 0.3,
    SourceCategory.other: 0.5,  # not in spec; defensive fallback for ambiguous extractions
}

AGE_PENALTY_YEARS = 3
AGE_PENALTY = 0.2


def confidence_score(
    category: SourceCategory,
    published_date: date | None,
    as_of: date,
) -> float:
    score = BASE_CONFIDENCE[category]

    if published_date is not None:
        age_years = (as_of - published_date).days / 365.25
        if age_years > AGE_PENALTY_YEARS:
            score -= AGE_PENALTY
    # published_date unknown: can't assess age, so no penalty — not a guess.

    return max(0.0, min(1.0, score))
