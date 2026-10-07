from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base


class PersonaAssignment(Base):
    hcp_id: UUID
    brand_id: UUID
    persona_id: UUID
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
