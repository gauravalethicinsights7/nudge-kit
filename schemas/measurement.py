"""specs/m8-measurement.md's output entities — Foundations' entity table
defers Outcome/Scorecard to this spec ('see specs/m8-measurement.md');
LiftEstimate, PriorUpdate and AssumptionReview aren't named there either but
are this spec's other explicit outputs.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field

from schemas.base import Base, StrictModel
from schemas.enums import Rung


class Outcome(Base):
    brand_id: UUID
    hcp_id: UUID | None = None
    segment_id: UUID | None = None
    period: str  # YYYY-MM
    engagement_index: float = Field(ge=0.0, le=100.0)
    rung: Rung | None = None
    nrx: float | None = None
    trx: float | None = None


class KpiResult(StrictModel):
    name: str
    category: Literal["activity", "engagement", "outcome"]
    actual: float
    plan: float | None = None
    variance: float | None = None  # actual - plan; None when plan is unknown
    rag: Literal["green", "amber", "red"] | None = None  # None when plan is unknown


class Scorecard(Base):
    brand_id: UUID
    period: str
    kpis: list[KpiResult] = Field(default_factory=list)


class LiftEstimate(Base):
    brand_id: UUID
    test_name: str
    effect: float
    ci_low: float
    ci_high: float
    method: Literal["did", "counterfactual_trend"]


class PriorUpdate(Base):
    """Tenant-level prior override — Base's own tenant_id/version fields are
    exactly the 'tenant-level, versioned' mechanism the spec asks for.
    packs/<market>/pack.yaml is never written to by this or any other code
    path (CLAUDE.md rule 5); this is a separate, overlay record."""

    brand_id: UUID
    prior_type: Literal["rung_transition", "curve_param", "fit_weight"]
    key: str  # e.g. a Rung value, a channel_ref, or a fit_weight name
    period: str  # YYYY-MM the update was computed from
    before: float
    after: float


class AssumptionCheck(StrictModel):
    assumption: str
    held: bool
    planned_value: float
    actual_value: float


class AssumptionReview(Base):
    brand_id: UUID
    period: str
    items: list[AssumptionCheck] = Field(default_factory=list)
