from __future__ import annotations

from uuid import UUID

from pydantic import Field

from schemas.base import Base


class RunRecord(Base):
    module: str
    inputs_hash: str
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    output_ids: list[UUID] = Field(default_factory=list)
    error: str | None = None
