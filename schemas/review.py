"""Per-object approve/reject/annotate — specs/blueprint's MLR reviewer flow
("Claims and messages: approve / reject / annotate"). Status stays
draft/approved/superseded (schemas.enums.Status) for every entity; a
rejection or comment is recorded here instead of inventing a fourth status
value that would touch every entity in the registry.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from schemas.base import StrictModel, utcnow
from schemas.enums import ReviewDecisionType


class ReviewDecision(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    brand_id: UUID
    entity_type: str
    object_id: UUID
    decision: ReviewDecisionType
    comment: str | None = None
    reviewer_user_id: UUID
    created_at: datetime = Field(default_factory=utcnow)
