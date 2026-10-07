from __future__ import annotations

from pydantic import Field

from schemas.base import Base, ProvMoney, StrictModel
from schemas.enums import CurveSource, Rung


class ResponseCurve(StrictModel):
    lambda_: float = Field(alias="lambda")
    alpha: float
    gamma: float
    beta: float | None = None
    source: CurveSource

    model_config = StrictModel.model_config | {"populate_by_name": True}


class Channel(Base):
    channel_ref: str  # id of the channel in packs/<market>/pack.yaml
    name: str
    unit: str
    unit_cost: ProvMoney | None = None
    capacity: float | None = None
    stage_fit: dict[Rung, float] = Field(default_factory=dict)
    curve: ResponseCurve
    compliance_rule_ids: list[str] = Field(default_factory=list)
    # M6 (specs/m6-channel-mix.md): "ResponseModel per channel (params, source
    # prior|fitted, diagnostics)" — diagnostics only when curve.source=fitted
    # (e.g. r_hat, periods_used); None for a pack-prior curve.
    diagnostics: dict | None = None
