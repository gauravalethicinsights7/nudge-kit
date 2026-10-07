from __future__ import annotations

from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from schemas.base import Base, ProvNumber, StrictModel
from schemas.enums import Access, Rung, Setting, Tier


class ExternalIds(StrictModel):
    npi: str | None = None
    mci_reg: str | None = None
    crm_id: str | None = None


class Geo(StrictModel):
    state: str | None = None
    city: str | None = None
    city_tier: str | None = None
    territory_id: str | None = None


class Consent(StrictModel):
    email: bool = False
    whatsapp: bool = False
    sms: bool = False


class HCP(Base):
    external_ids: ExternalIds
    name_hash: str
    specialty: str
    setting: Setting
    geo: Geo
    potential: ProvNumber
    brand_share: ProvNumber
    access: Access
    consent: Consent
    persona_id: UUID | None = None
    # Raw signals behind models.scores.estimate_potential, per pack.yaml's
    # potential_proxies.signals (added for M2 — Foundations didn't anticipate
    # these). None when ingest has nothing better than the categorical proxy.
    patient_volume_estimate: float | None = None
    rep_class: str | None = None


class Segment(Base):
    brand_id: UUID
    name: str
    rule: dict[str, Any]
    tier: Tier
    hcp_count: int
    total_potential: float
    avg_share: float
    target_share: float
    intent: str | None = None
    # specs/m2-segmentation.md: "flag mode=segment_only" when built without
    # HCP-level rows (MarketLandscape/pack categories only).
    mode: Literal["hcp_level", "segment_only"] = "hcp_level"


class AdoptionState(Base):
    hcp_id: UUID
    brand_id: UUID
    rung: Rung
    entered_on: date
    p_move_up: float = Field(ge=0.0, le=1.0)
    measured: bool = False
    # Confidence in the *current* rung assignment itself — distinct from
    # p_move_up (probability of moving to the *next* rung). Added for M2's
    # "unknown -> aware, confidence 0.3" fallback (specs/m2-segmentation.md).
    rung_confidence: float = Field(ge=0.0, le=1.0, default=1.0)
