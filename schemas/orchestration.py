"""specs/m7-orchestration.md's JourneyRule/Action outputs — Foundations'
entity table defers both to this spec ('see specs/m7-orchestration.md').
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from schemas.base import Base, StrictModel
from schemas.enums import ActionStatus


class JourneyStepRule(StrictModel):
    channel: str
    content_ref: str | None = None  # None when no approved content exists yet — see ContentBrief
    wait_days: int = 0
    condition: str | None = None


class Escalation(StrictModel):
    signal: str
    action: str


class JourneyRule(Base):
    brand_id: UUID
    segment_id: UUID
    persona_id: UUID
    entry_criteria: dict = Field(default_factory=dict)
    steps: list[JourneyStepRule] = Field(default_factory=list)
    escalation: list[Escalation] = Field(default_factory=list)
    exit_signal: str


class Action(Base):
    brand_id: UUID
    hcp_id: UUID
    channel: str
    content_ref: str | None = None
    suggested_date: date
    reason: str
    score: float
    # NOT `status` — Base already defines that for the draft/approved/
    # superseded human-checkpoint workflow (CLAUDE.md rule 8). This is a
    # distinct, Action-specific lifecycle (suggested/accepted/dismissed/done,
    # spec: "Feedback: accepted/dismissed/done events stored for retraining").
    action_status: ActionStatus = ActionStatus.suggested
