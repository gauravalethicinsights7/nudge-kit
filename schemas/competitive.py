from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from schemas.base import Base, ProvMoney, StrictModel
from schemas.enums import ClaimStrength, Driver


class SharePoint(StrictModel):
    period: str  # YYYY-MM
    share: float


class SovPoint(StrictModel):
    period: str  # YYYY-MM
    channel: str
    value: float


class CompetitorClaim(StrictModel):
    driver: Driver
    text: str
    strength: ClaimStrength
    evidence_id: UUID
    # specs/m4-competitive.md rule: "Comparative claims for our brand are
    # flagged requires_mlr_comparative=True." Only meaningful on claims
    # attributed to our own brand's Competitor-shaped entry, not real
    # competitors — added here since CompetitorClaim is the one place a
    # claim's text/driver/strength already live.
    requires_mlr_comparative: bool = False


class CompetitorEvent(StrictModel):
    date: date
    type: str
    text: str
    evidence_id: UUID


class Competitor(Base):
    brand_id: UUID
    competitor_brand: str
    company: str
    share_trend: list[SharePoint] = Field(default_factory=list)
    sov: list[SovPoint] = Field(default_factory=list)
    claims: list[CompetitorClaim] = Field(default_factory=list)
    price: ProvMoney | None = None
    events: list[CompetitorEvent] = Field(default_factory=list)


class MessageGridCell(StrictModel):
    driver: Driver
    brand: str
    strength: ClaimStrength


class Whitespace(StrictModel):
    driver: Driver
    personas: list[str] = Field(default_factory=list)
    rationale: str


class MessageMap(Base):
    brand_id: UUID
    grid: list[MessageGridCell] = Field(default_factory=list)
    whitespace: list[Whitespace] = Field(default_factory=list)
    parity_risks: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)
