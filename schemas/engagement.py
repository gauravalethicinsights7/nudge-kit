"""specs/m8-measurement.md needs 'engagement events' as an input to compute
the Engagement Index — M7 flagged the same gap and deferred it (recency
decay defaulted to neutral). M8 is where it actually has to exist.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from schemas.base import Base


class EngagementEvent(Base):
    brand_id: UUID
    hcp_id: UUID
    channel: str
    depth: str  # must be a key in pack.engagement_depth (delivered/opened/clicked/attended/requested_followup)
    occurred_at: date
    period: str  # YYYY-MM
