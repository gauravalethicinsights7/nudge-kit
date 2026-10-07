from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base, StrictModel


class FitComponents(StrictModel):
    """The four terms of specs/m6-channel-mix.md's fit formula, kept alongside
    the combined score for transparency (which term drove a low/high fit)."""

    affinity: float
    access: float
    stage_fit: float
    content_fit: float


class ChannelFit(Base):
    brand_id: UUID
    segment_id: UUID
    persona_id: UUID | None = None  # per spec: "per HCP (or per segment x persona)"
    channel_id: str
    fit_score: float = Field(ge=0.0, le=1.0)
    components: FitComponents
