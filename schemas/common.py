from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import StrictModel


class EvidencedText(StrictModel):
    """The recurring 'text + evidence_ids' pattern used across entities."""

    text: str
    evidence_ids: list[UUID] = Field(default_factory=list)
