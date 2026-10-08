from __future__ import annotations

from typing import Literal
from uuid import UUID

from schemas.base import Base, StrictModel


class ResearchGap(Base):
    brand_id: UUID
    block: str  # question_bank.yaml block name
    question: str
    best_confidence: float = 0.0
    reason: Literal["unanswered", "low_confidence"]
    notes: str | None = None


# ---- question-bank coverage (read model, not persisted) ----
# Every brand is researched against the same fixed bank, so coverage is what
# makes "we were thorough" checkable rather than asserted. Derived on read
# from the gaps the agent recorded; nothing new is stored.


class QuestionCoverage(StrictModel):
    question: str
    status: Literal["answered", "partial", "gap"]
    # None when answered — no gap row was written, so no confidence was kept.
    best_confidence: float | None = None


class QuestionBlockCoverage(StrictModel):
    block: str
    questions: list[QuestionCoverage]


class QuestionBankCoverage(StrictModel):
    blocks: list[QuestionBlockCoverage]
    threshold: float
    total: int
    answered: int
    partial: int
    gap: int
    # False before M1 has ever run, so the UI can say "not researched yet"
    # instead of reporting 28 gaps as though they were findings.
    has_run: bool
