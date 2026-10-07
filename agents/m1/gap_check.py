from __future__ import annotations

from uuid import UUID

from agents.m1.synthesiser import SynthesisResult
from schemas.research import ResearchGap

GAP_CONFIDENCE_THRESHOLD = 0.5  # per specs/m1-research.md: "confidence >= 0.5"


def find_gaps(
    brand_id: UUID,
    question_bank: dict[str, list[str]],
    synthesis: SynthesisResult,
) -> list[ResearchGap]:
    """Deterministic per CLAUDE.md rule 1: the >=0.5 threshold lives here, not
    in a prompt. Any question the synthesiser didn't report coverage for at
    all (LLM omission, not just an explicit answered=False) is treated as
    unanswered — the question bank, not the LLM's output, is authoritative
    for what needs covering."""
    coverage_by_question = {(c.block, c.question): c for c in synthesis.question_coverage}

    gaps: list[ResearchGap] = []
    for block, questions in question_bank.items():
        for question in questions:
            coverage = coverage_by_question.get((block, question))

            if coverage is None or not coverage.answered:
                gaps.append(
                    ResearchGap(
                        brand_id=brand_id,
                        block=block,
                        question=question,
                        best_confidence=coverage.confidence if coverage else 0.0,
                        reason="unanswered",
                    )
                )
            elif coverage.confidence < GAP_CONFIDENCE_THRESHOLD:
                gaps.append(
                    ResearchGap(
                        brand_id=brand_id,
                        block=block,
                        question=question,
                        best_confidence=coverage.confidence,
                        reason="low_confidence",
                    )
                )

    return gaps
