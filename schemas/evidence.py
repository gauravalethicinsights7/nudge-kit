from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from schemas.base import Base, Prov
from schemas.enums import EvidenceType, MlrStatus, SourceCategory


class Evidence(Base, Prov):
    brand_id: UUID
    type: EvidenceType
    claim: str = Field(max_length=500)
    quote: str | None = None
    source_url: str | None = None
    publisher: str | None = None
    published_date: date | None = None
    entities_mentioned: list[str] = Field(default_factory=list)
    mlr_status: MlrStatus = MlrStatus.none
    embedding: list[float] | None = None
    # Which bucket drove `confidence` (models/evidence.py::confidence_score) —
    # kept for auditability; None for evidence seeded without categorization
    # (e.g. Foundations' fixture loader).
    source_category: SourceCategory | None = None
