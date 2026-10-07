from __future__ import annotations

from typing import Literal
from uuid import UUID

from schemas.base import Base


class ResearchGap(Base):
    brand_id: UUID
    block: str  # question_bank.yaml block name
    question: str
    best_confidence: float = 0.0
    reason: Literal["unanswered", "low_confidence"]
    notes: str | None = None
