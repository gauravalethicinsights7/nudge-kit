from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base, StrictModel


class TargetListEntry(StrictModel):
    hcp_id: UUID
    rank: int
    opportunity_score: float
    reachability: float
    reason: str


class TargetList(Base):
    brand_id: UUID
    segment_id: UUID
    entries: list[TargetListEntry] = Field(default_factory=list)
