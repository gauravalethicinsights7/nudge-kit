from __future__ import annotations

from pydantic import Field

from schemas.base import StrictModel
from schemas.enums import Market


class CurvePrior(StrictModel):
    lambda_: float = Field(alias="lambda")
    alpha: float
    gamma: float
    beta: float | None = None

    model_config = StrictModel.model_config | {"populate_by_name": True}


class PackChannel(StrictModel):
    id: str
    name: str
    unit: str
    unit_cost: float | None = None
    capacity_rule: str | None = None
    capacity_defaults: dict[str, float] | None = None
    stage_fit: dict[str, float]
    curve_prior: CurvePrior
    requires_consent: bool
    consent_field: str | None = None
    notes: str | None = None


class DataSource(StrictModel):
    id: str
    name: str
    origin: str
    grain: str
    licensed: bool | None = None


class ComplianceRule(StrictModel):
    id: str
    rule: str
    applies_to: list[str]
    severity: str


class PotentialProxies(StrictModel):
    specialty_weight: dict[str, float] = Field(default_factory=dict)
    setting_weight: dict[str, float] = Field(default_factory=dict)
    city_tier_weight: dict[str, float] = Field(default_factory=dict)
    signals: list[str] = Field(default_factory=list)


class Priors(StrictModel):
    rung_transition_monthly: dict[str, float] = Field(default_factory=dict)
    persistence_6m_default: float | None = None
    benchmark_confidence: float


class TierRule(StrictModel):
    potential_pctl_min: float | None = None
    potential_pctl_max: float | None = None
    rungs: list[str] | None = None
    reachability_min: float | None = None


class RungRule(StrictModel):
    """specs/m2-segmentation.md's Rx/engagement-based rung assignment rules.
    Not defined by either shipped pack today (models/scores.py::assign_rung
    falls back to unknown->aware when this is absent) — declared here so a
    market pack CAN define one later without Pack's extra='forbid' rejecting
    it at load time."""

    rule: dict[str, str]
    rung: str


class Kpis(StrictModel):
    leading: list[str] = Field(default_factory=list)
    lagging: list[str] = Field(default_factory=list)


class Pack(StrictModel):
    """Validated form of packs/<market>/pack.yaml. Unknown top-level keys fail loudly
    (schemas.pack.Pack has extra='forbid' via StrictModel) so a market-pack typo is
    caught at load time rather than silently ignored.
    """

    market: Market
    currency: str = Field(min_length=3, max_length=3)
    default_maturity_stage: int
    fiscal_year_start_month: int
    channels: list[PackChannel]
    fit_weights: dict[str, float]
    access_weights: dict[str, float]
    frequency_caps: dict[str, int]
    suppress_after: int
    potential_proxies: PotentialProxies | None = None
    data_sources: list[DataSource]
    compliance_rules: list[ComplianceRule]
    signals: list[str]
    engagement_depth: dict[str, float]
    priors: Priors
    tiers: dict[str, TierRule]
    kpis: Kpis
    # Not present in either pack.yaml today (both are v0.1 placeholders); kept optional
    # so `pack.benchmarks` (named in specs/00-foundations.md) resolves to None rather
    # than AttributeError, and validates cleanly once a pack adds real benchmark data.
    benchmarks: dict | None = None
    rung_rules: list[RungRule] | None = None
