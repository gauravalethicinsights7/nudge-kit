"""BrandPlan — the last entity Foundations deferred ("see specs/m5-brand-plan.md").
One nested model per section of that spec's Output table.
"""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from schemas.base import Base, ProvMoney, StrictModel
from schemas.common import EvidencedText
from schemas.enums import Driver, Rung

REQUIRED_PILLAR_COUNT = 3


class Situation(StrictModel):
    summary: str
    key_facts: list[EvidencedText] = Field(default_factory=list)


class KeyIssue(StrictModel):
    id: UUID
    statement: str
    barrier: str
    segment_id: UUID | None = None
    revenue_at_stake: ProvMoney
    evidence_ids: list[UUID] = Field(default_factory=list)


class Imperative(StrictModel):
    id: UUID
    title: str
    key_issue_ids: list[UUID] = Field(min_length=1)  # spec: "every imperative links >= 1 key issue"
    segment_id: UUID | None = None
    from_rung: Rung
    to_rung: Rung


class Positioning(StrictModel):
    target: str
    frame_of_reference: str
    point_of_difference: str
    # Added so "POD in whitespace" (spec's quality bar) is mechanically
    # checkable against MessageMap.whitespace, not just judged from prose.
    driver: Driver
    reasons_to_believe: list[EvidencedText] = Field(default_factory=list)


class MessagePillar(StrictModel):
    driver: Driver
    message: str
    proofs: list[UUID] = Field(min_length=1)  # spec: ">= 1 proof evidence_id"


class MessageHouse(StrictModel):
    core: str
    pillars: list[MessagePillar] = Field(min_length=REQUIRED_PILLAR_COUNT, max_length=REQUIRED_PILLAR_COUNT)
    by_persona: dict[UUID, str] = Field(default_factory=dict)


class Objective(StrictModel):
    imperative_id: UUID
    metric: str
    baseline: float
    target: float
    due: date
    segment_id: UUID | None = None


class StrategyTactic(StrictModel):
    imperative_id: UUID
    segments: list[UUID] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    channel_sequence_ref: str | None = None  # filled in after M6
    content_needs: list[str] = Field(default_factory=list)


class KpiNode(StrictModel):
    name: str
    target: float | None = None


class KpiTree(StrictModel):
    leading: list[KpiNode] = Field(default_factory=list)
    lagging: list[KpiNode] = Field(default_factory=list)


class ForecastAssumption(StrictModel):
    name: str
    value: float
    confidence: float = Field(ge=0.0, le=1.0)


class ForecastScenario(StrictModel):
    delta_nrx: float
    revenue: ProvMoney
    roi: float | None = None  # None when incremental_spend is unknown, never fabricated
    assumptions: list[ForecastAssumption] = Field(default_factory=list)


class Forecast(StrictModel):
    base: ForecastScenario
    upside: ForecastScenario
    downside: ForecastScenario


class BudgetLine(StrictModel):
    imperative_id: UUID | None = None
    channel_id: str | None = None
    amount: ProvMoney
    # Filled in once M6 actually runs (specs/m6-channel-mix.md: "marginal ROI
    # per channel; position on curve"); None on M5's own placeholder lines.
    marginal_roi: float | None = None
    position: Literal["under", "efficient", "saturated"] | None = None


class Budget(StrictModel):
    lines: list[BudgetLine] = Field(default_factory=list)
    placeholder: bool = True  # spec: "from M6 (placeholder until run)"


class RiskTest(StrictModel):
    assumption: str
    confidence: float = Field(ge=0.0, le=1.0)
    test_design: str
    stop_go: str


class ComplianceFlag(StrictModel):
    item: str
    rule_id: str
    severity: str  # matches packs/*/pack.yaml compliance_rules[].severity ("block" | "warn")


class BrandPlan(Base):
    brand_id: UUID
    plan_horizon_months: int = 12
    situation: Situation
    # Spec targets 4-6 key_issues / 3-5 imperatives, but that's not always
    # satisfiable — a sparse upstream Segment[] (e.g. only 3 tiers came out of
    # M2) can legitimately yield fewer. Enforcing a hard minimum here would
    # turn an honest "not enough real data" case into an unretriable failure
    # (CLAUDE.md rule 2's retry loop is for fixable LLM mistakes, not for
    # demanding key issues that don't exist). Targets are enforced where
    # they're actually controllable: agents/m5/agent.py's ranking/prompting.
    key_issues: list[KeyIssue] = Field(min_length=1)
    imperatives: list[Imperative] = Field(min_length=1)
    positioning: Positioning
    message_house: MessageHouse
    objectives: list[Objective] = Field(default_factory=list)
    strategies_tactics: list[StrategyTactic] = Field(default_factory=list)
    kpi_tree: KpiTree
    forecast: Forecast
    budget: Budget = Field(default_factory=Budget)
    risks_tests: list[RiskTest] = Field(default_factory=list)
    compliance_flags: list[ComplianceFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_imperatives_reference_real_key_issues(self) -> "BrandPlan":
        key_issue_ids = {ki.id for ki in self.key_issues}
        for imperative in self.imperatives:
            unknown = set(imperative.key_issue_ids) - key_issue_ids
            if unknown:
                raise ValueError(
                    f"imperative '{imperative.title}' references unknown key_issue_ids: "
                    f"{sorted(str(i) for i in unknown)}"
                )
        return self
