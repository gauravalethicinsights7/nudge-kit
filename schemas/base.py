from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from schemas.enums import Origin, Status


def utcnow() -> datetime:
    """Naive UTC now — matches the Postgres `timestamp without time zone` columns
    in store/orm.py. Avoids the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StrictModel(BaseModel):
    """Common config: unknown fields are a bug, not something to silently drop."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class Base(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None  # None = shareable external data, per CLAUDE.md rule 7
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    status: Status = Status.draft
    version: int = 1


class Prov(StrictModel):
    """Provenance mixin: every number/claim carries source, origin, recency, confidence."""

    source: str
    origin: Origin
    as_of: date
    confidence: float = Field(ge=0.0, le=1.0)


class ProvNumber(Prov):
    value: float
    low: float | None = None
    high: float | None = None


class ProvMoney(ProvNumber):
    currency: str = Field(min_length=3, max_length=3)
