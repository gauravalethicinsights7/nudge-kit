from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base, ProvMoney, StrictModel


class ChannelAllocation(StrictModel):
    touches_per_month: float
    spend: ProvMoney
    share_of_budget: float = Field(ge=0.0, le=1.0)


class ChannelPlan(Base):
    brand_id: UUID
    # {segment_id: {channel_id: allocation}} per spec's own output shape.
    allocations: dict[UUID, dict[str, ChannelAllocation]] = Field(default_factory=dict)
    sequence_template_ref: str | None = None
