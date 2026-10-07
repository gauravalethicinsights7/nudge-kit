"""specs/m7-orchestration.md needs a content module library (mlr_status,
on/off-label, comparative-claim flags) as an input, but nothing before this
session built one — Foundations' entity table doesn't define it either. Added
here, same as M6 adding the Channel-building plumbing nothing built before.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base
from schemas.enums import Driver, MlrStatus


class ContentModule(Base):
    brand_id: UUID
    name: str
    channel_refs: list[str] = Field(default_factory=list)
    driver: Driver
    persona_ids: list[UUID] = Field(default_factory=list)  # empty = usable for any persona
    claim: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    format: str
    mlr_status: MlrStatus = MlrStatus.none
    on_label: bool = True
    is_comparative: bool = False
    comparative_approved: bool = False
    # India UCPMP "no patient-directed Rx brand promotion" (specs/m7's
    # guardrails) — this module is written for/reaches patients, not HCPs.
    patient_directed: bool = False
    # UCPMP gift/sample/reminder-item numeric caps can't be computed from
    # anything in this build (no quantity-tracking data exists) — this is a
    # pre-computed flag a real gift/sample-tracking system would set, which
    # the guardrail simply respects. See models/guardrails.py.
    exceeds_pack_limit: bool = False


class ContentBrief(Base):
    """specs/m7-orchestration.md output: 'modules needed but missing'."""

    brand_id: UUID
    driver: Driver
    persona_id: UUID | None = None
    channel: str
    format: str
    claim_needed: str
    reason: str
