from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base, ProvMoney, ProvNumber, StrictModel
from schemas.common import EvidencedText


class PatientFunnel(StrictModel):
    """Each stage is independently optional: M1's rule is 'never invent a number;
    if missing, leave null and add to gaps' — one stage can be known (e.g.
    prevalence) while another (e.g. controlled) isn't."""

    prevalent: ProvNumber | None = None
    diagnosed: ProvNumber | None = None
    treated: ProvNumber | None = None
    controlled: ProvNumber | None = None


class MarketLandscape(Base):
    brand_id: UUID
    patient_funnel: PatientFunnel | None = None
    market_size: ProvMoney | None = None
    growth_pct: ProvNumber | None = None
    paradigm: EvidencedText | None = None
    access_summary: str | None = None
    unmet_needs: list[str] = Field(default_factory=list)
    key_facts: list[EvidencedText] = Field(default_factory=list)
