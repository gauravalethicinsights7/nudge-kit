from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from schemas.base import utcnow
from store.db import OrmBase
from store.embeddings import EMBEDDING_DIM


class BrandORM(OrmBase):
    __tablename__ = "brand"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    name: Mapped[str] = mapped_column(String, nullable=False)
    molecule: Mapped[str] = mapped_column(String, nullable=False)
    indication: Mapped[str] = mapped_column(String, nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(20), nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    price_band: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class EvidenceORM(OrmBase):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    source: Mapped[str] = mapped_column(String, nullable=False)
    origin: Mapped[str] = mapped_column(String(20), nullable=False)
    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    claim: Mapped[str] = mapped_column(String(500), nullable=False)
    quote: Mapped[str | None] = mapped_column(String, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    entities_mentioned: Mapped[list] = mapped_column(JSONB, default=list)
    mlr_status: Mapped[str] = mapped_column(String(20), default="none")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    source_category: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Dedup keys, per specs/00-foundations.md: "de-duplicate on normalised URL + claim hash"
    normalized_url: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    claim_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class MarketLandscapeORM(OrmBase):
    __tablename__ = "market_landscape"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    # Nested provenance-bearing substructures stored as JSONB, same pattern as
    # Evidence.entities_mentioned — each is the corresponding Pydantic
    # sub-model's .model_dump(mode="json"), or null if that stage is unknown.
    patient_funnel: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    market_size: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    growth_pct: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    paradigm: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    access_summary: Mapped[str | None] = mapped_column(String, nullable=True)
    unmet_needs: Mapped[list] = mapped_column(JSONB, default=list)
    key_facts: Mapped[list] = mapped_column(JSONB, default=list)


class ResearchGapORM(OrmBase):
    __tablename__ = "research_gap"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    block: Mapped[str] = mapped_column(String(50), nullable=False)
    question: Mapped[str] = mapped_column(String, nullable=False)
    best_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class AdoptionStateORM(OrmBase):
    __tablename__ = "adoption_state"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    # No hcp table exists yet (HCP is transient, loaded fresh from CSV each
    # run) — hcp_id is a plain UUID, not an enforced FK.
    hcp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    rung: Mapped[str] = mapped_column(String(20), nullable=False)
    entered_on: Mapped[date] = mapped_column(Date, nullable=False)
    p_move_up: Mapped[float] = mapped_column(Float, nullable=False)
    measured: Mapped[bool] = mapped_column(Boolean, default=False)
    rung_confidence: Mapped[float] = mapped_column(Float, default=1.0)


class SegmentORM(OrmBase):
    __tablename__ = "segment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    rule: Mapped[dict] = mapped_column(JSONB, default=dict)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    hcp_count: Mapped[int] = mapped_column(Integer, default=0)
    total_potential: Mapped[float] = mapped_column(Float, default=0.0)
    avg_share: Mapped[float] = mapped_column(Float, default=0.0)
    target_share: Mapped[float] = mapped_column(Float, default=0.0)
    intent: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String(20), default="hcp_level")


class TargetListORM(OrmBase):
    __tablename__ = "target_list"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segment.id"), nullable=False
    )
    entries: Mapped[list] = mapped_column(JSONB, default=list)


class PersonaORM(OrmBase):
    __tablename__ = "persona"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    beliefs: Mapped[list] = mapped_column(JSONB, default=list)
    drivers_ranked: Mapped[list] = mapped_column(JSONB, default=list)
    barriers_by_rung: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence_needs: Mapped[list] = mapped_column(JSONB, default=list)
    channel_affinity: Mapped[dict] = mapped_column(JSONB, default=dict)
    influence_network: Mapped[list] = mapped_column(JSONB, default=list)
    share_of_universe: Mapped[float] = mapped_column(Float, nullable=False)
    share_of_potential: Mapped[float] = mapped_column(Float, nullable=False)
    derivation: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JSONB, default=list)
    assumption: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class JourneyMapORM(OrmBase):
    __tablename__ = "journey_map"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    persona_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persona.id"), nullable=True
    )
    steps: Mapped[list] = mapped_column(JSONB, default=list)


class PersonaAssignmentORM(OrmBase):
    __tablename__ = "persona_assignment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    # No hcp table exists yet (see AdoptionStateORM) — hcp_id is a plain UUID.
    hcp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persona.id"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class CompetitorORM(OrmBase):
    __tablename__ = "competitor"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    competitor_brand: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    share_trend: Mapped[list] = mapped_column(JSONB, default=list)
    sov: Mapped[list] = mapped_column(JSONB, default=list)
    claims: Mapped[list] = mapped_column(JSONB, default=list)
    price: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    events: Mapped[list] = mapped_column(JSONB, default=list)


class MessageMapORM(OrmBase):
    __tablename__ = "message_map"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    grid: Mapped[list] = mapped_column(JSONB, default=list)
    whitespace: Mapped[list] = mapped_column(JSONB, default=list)
    parity_risks: Mapped[list] = mapped_column(JSONB, default=list)
    threats: Mapped[list] = mapped_column(JSONB, default=list)


class EarlyWarningSignalORM(OrmBase):
    __tablename__ = "early_warning_signal"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    detection_rule: Mapped[str] = mapped_column(String, nullable=False)
    affected_segments: Mapped[list] = mapped_column(JSONB, default=list)
    evidence_ids: Mapped[list] = mapped_column(JSONB, default=list)


class BrandPlanORM(OrmBase):
    __tablename__ = "brand_plan"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    plan_horizon_months: Mapped[int] = mapped_column(Integer, default=12)
    # Every section below is a nested Pydantic structure with its own
    # sub-models — stored as JSONB in one blob per section, the same pattern
    # used throughout this store (e.g. MarketLandscapeORM's patient_funnel).
    situation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    key_issues: Mapped[list] = mapped_column(JSONB, default=list)
    imperatives: Mapped[list] = mapped_column(JSONB, default=list)
    positioning: Mapped[dict] = mapped_column(JSONB, nullable=False)
    message_house: Mapped[dict] = mapped_column(JSONB, nullable=False)
    objectives: Mapped[list] = mapped_column(JSONB, default=list)
    strategies_tactics: Mapped[list] = mapped_column(JSONB, default=list)
    kpi_tree: Mapped[dict] = mapped_column(JSONB, nullable=False)
    forecast: Mapped[dict] = mapped_column(JSONB, nullable=False)
    budget: Mapped[dict] = mapped_column(JSONB, default=dict)
    risks_tests: Mapped[list] = mapped_column(JSONB, default=list)
    compliance_flags: Mapped[list] = mapped_column(JSONB, default=list)


class ChannelORM(OrmBase):
    __tablename__ = "channel"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    channel_ref: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    unit_cost: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    capacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    stage_fit: Mapped[dict] = mapped_column(JSONB, default=dict)
    curve: Mapped[dict] = mapped_column(JSONB, nullable=False)
    compliance_rule_ids: Mapped[list] = mapped_column(JSONB, default=list)
    diagnostics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ChannelFitORM(OrmBase):
    __tablename__ = "channel_fit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    persona_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    channel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ChannelPlanORM(OrmBase):
    __tablename__ = "channel_plan"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False
    )
    allocations: Mapped[dict] = mapped_column(JSONB, default=dict)
    sequence_template_ref: Mapped[str | None] = mapped_column(String, nullable=True)


class ContentModuleORM(OrmBase):
    __tablename__ = "content_module"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    channel_refs: Mapped[list] = mapped_column(JSONB, default=list)
    driver: Mapped[str] = mapped_column(String(50), nullable=False)
    persona_ids: Mapped[list] = mapped_column(JSONB, default=list)
    claim: Mapped[str] = mapped_column(String, nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JSONB, default=list)
    format: Mapped[str] = mapped_column(String, nullable=False)
    mlr_status: Mapped[str] = mapped_column(String(20), default="none")
    on_label: Mapped[bool] = mapped_column(Boolean, default=True)
    is_comparative: Mapped[bool] = mapped_column(Boolean, default=False)
    comparative_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    patient_directed: Mapped[bool] = mapped_column(Boolean, default=False)
    exceeds_pack_limit: Mapped[bool] = mapped_column(Boolean, default=False)


class JourneyRuleORM(OrmBase):
    __tablename__ = "journey_rule"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    persona_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entry_criteria: Mapped[dict] = mapped_column(JSONB, default=dict)
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    escalation: Mapped[list] = mapped_column(JSONB, default=list)
    exit_signal: Mapped[str] = mapped_column(String, nullable=False)


class ActionORM(OrmBase):
    __tablename__ = "action"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    hcp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    content_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    suggested_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    action_status: Mapped[str] = mapped_column(String(20), default="suggested")


class EngagementEventORM(OrmBase):
    __tablename__ = "engagement_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    hcp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    depth: Mapped[str] = mapped_column(String(50), nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)


class OutcomeORM(OrmBase):
    __tablename__ = "outcome"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    hcp_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    segment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    engagement_index: Mapped[float] = mapped_column(Float, nullable=False)
    rung: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nrx: Mapped[float | None] = mapped_column(Float, nullable=True)
    trx: Mapped[float | None] = mapped_column(Float, nullable=True)


class ScorecardORM(OrmBase):
    __tablename__ = "scorecard"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    kpis: Mapped[list] = mapped_column(JSONB, default=list)


class LiftEstimateORM(OrmBase):
    __tablename__ = "lift_estimate"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    effect: Mapped[float] = mapped_column(Float, nullable=False)
    ci_low: Mapped[float] = mapped_column(Float, nullable=False)
    ci_high: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)


class PriorUpdateORM(OrmBase):
    __tablename__ = "prior_update"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    prior_type: Mapped[str] = mapped_column(String(30), nullable=False)
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    before: Mapped[float] = mapped_column(Float, nullable=False)
    after: Mapped[float] = mapped_column(Float, nullable=False)


class AssumptionReviewORM(OrmBase):
    __tablename__ = "assumption_review"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    items: Mapped[list] = mapped_column(JSONB, default=list)


class RunRecordORM(OrmBase):
    __tablename__ = "run_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    module: Mapped[str] = mapped_column(String(50), nullable=False)
    inputs_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_versions: Mapped[dict] = mapped_column(JSONB, default=dict)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    output_ids: Mapped[list] = mapped_column(JSONB, default=list)
    error: Mapped[str | None] = mapped_column(String, nullable=True)


class TenantORM(OrmBase):
    __tablename__ = "tenant"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserORM(OrmBase):
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserBrandAccessORM(OrmBase):
    __tablename__ = "user_brand_access"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False)
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ReviewDecisionORM(OrmBase):
    __tablename__ = "review_decision"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class JobORM(OrmBase):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand.id"), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UploadORM(OrmBase):
    """Uploaded Data Hub files, stored as bytes in the database rather than on
    disk. The engine re-reads these on every module run, and the API now runs
    on hosts with an ephemeral filesystem — a container restart would
    otherwise silently drop every upload and break M2/M6/M7/M8 until the user
    noticed and re-uploaded. See api/uploads_store.py, which still hands
    callers a Path by materializing the bytes into a local cache."""

    __tablename__ = "upload"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand.id"), primary_key=True
    )
    kind: Mapped[str] = mapped_column(String(50), primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
