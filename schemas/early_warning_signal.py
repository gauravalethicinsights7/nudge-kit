from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field

from schemas.base import Base

EarlyWarningType = Literal["launch", "price_cut", "generic_entry", "guideline_change"]


class EarlyWarningSignal(Base):
    brand_id: UUID
    type: EarlyWarningType
    detection_rule: str  # natural-language: M7's rule engine doesn't exist yet
    affected_segments: list[str] = Field(default_factory=list)  # descriptive labels, not FK'd
    evidence_ids: list[UUID] = Field(default_factory=list)
