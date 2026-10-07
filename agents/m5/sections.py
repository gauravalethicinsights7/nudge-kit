"""The seven LLM-generated sections of a BrandPlan (specs/m5-brand-plan.md's
Output table). Each call is validated against real upstream ids/drivers via
llm.client.call's validation_context — the same mechanism M1/M3/M4 used: a
hallucinated evidence_id, key_issue_id, or off-whitespace POD is a validation
error that retries, not a silent bad output.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationInfo, model_validator

from llm.client import call
from models.plan import KeyIssueCandidate
from schemas.brand import Brand
from schemas.brand_plan import (
    Imperative,
    KeyIssue,
    MessageHouse,
    MessagePillar,
    Positioning,
    Situation,
    StrategyTactic,
)
from schemas.common import EvidencedText
from schemas.competitive import MessageMap
from schemas.enums import Driver, Rung
from schemas.evidence import Evidence
from schemas.market_landscape import MarketLandscape
from schemas.persona import Persona

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _valid_evidence_ids(evidence: list[Evidence]) -> set[UUID]:
    return {e.id for e in evidence}


# ---- 1. situation ----


def build_situation(
    brand: Brand, market_landscape: MarketLandscape | None, evidence: list[Evidence], *, run_record_repo=None
) -> Situation:
    landscape_summary = (
        json.dumps(market_landscape.model_dump(mode="json"), default=str) if market_landscape else "none available"
    )
    return call(
        "situation",
        {"brand_name": brand.name, "market_landscape_summary": landscape_summary},
        Situation,
        model_tier="standard",
        module="m5_situation",
        run_record_repo=run_record_repo,
        validation_context={"valid_evidence_ids": _valid_evidence_ids(evidence)},
        prompts_dir=PROMPTS_DIR,
    )


# ---- 2. key_issues (models/plan.py ranks; LLM words) ----


class _KeyIssueWording(BaseModel):
    statement: str
    barrier: str
    evidence_ids: list[UUID] = Field(default_factory=list)


class _KeyIssuesWordingList(BaseModel):
    issues: list[_KeyIssueWording]

    @model_validator(mode="after")
    def _check_count_and_evidence(self, info: ValidationInfo) -> "_KeyIssuesWordingList":
        context = info.context or {}
        expected_count = context.get("expected_count")
        if expected_count is not None and len(self.issues) != expected_count:
            raise ValueError(f"expected exactly {expected_count} issues, got {len(self.issues)}")
        valid_ids = context.get("valid_evidence_ids")
        if valid_ids is not None:
            cited = {i for issue in self.issues for i in issue.evidence_ids}
            invented = cited - set(valid_ids)
            if invented:
                raise ValueError(f"cited evidence_ids not found: {sorted(str(i) for i in invented)}")
        return self


def word_key_issues(
    brand: Brand, candidates: list[KeyIssueCandidate], evidence: list[Evidence], *, run_record_repo=None
) -> list[KeyIssue]:
    if not candidates:
        return []

    candidates_summary = "\n".join(
        f"{i}. segment='{c.segment.name}' (tier={c.segment.tier.value}), "
        f"revenue_at_stake={c.revenue_at_stake.value:.0f} {c.revenue_at_stake.currency}"
        for i, c in enumerate(candidates)
    )
    evidence_summary = "\n".join(f"[{e.id}] {e.claim}" for e in evidence[:100]) or "none available"

    result = call(
        "key_issues",
        {"brand_name": brand.name, "candidates_summary": candidates_summary, "evidence_summary": evidence_summary},
        _KeyIssuesWordingList,
        model_tier="standard",
        module="m5_key_issues",
        run_record_repo=run_record_repo,
        validation_context={"expected_count": len(candidates), "valid_evidence_ids": _valid_evidence_ids(evidence)},
        prompts_dir=PROMPTS_DIR,
    )
    return [
        KeyIssue(
            id=uuid4(),
            statement=wording.statement,
            barrier=wording.barrier,
            segment_id=candidate.segment.id,
            revenue_at_stake=candidate.revenue_at_stake,
            evidence_ids=wording.evidence_ids,
        )
        for candidate, wording in zip(candidates, result.issues)
    ]


# ---- 3. imperatives (LLM, constrained to key issues) ----


class _ImperativeDraft(BaseModel):
    title: str
    key_issue_ids: list[UUID] = Field(min_length=1)
    segment_id: UUID | None = None
    from_rung: Rung
    to_rung: Rung


class _ImperativesDraftList(BaseModel):
    imperatives: list[_ImperativeDraft] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_key_issue_ids(self, info: ValidationInfo) -> "_ImperativesDraftList":
        context = info.context or {}
        valid_ids = context.get("valid_key_issue_ids")
        if valid_ids is not None:
            cited = {i for imp in self.imperatives for i in imp.key_issue_ids}
            invented = cited - set(valid_ids)
            if invented:
                raise ValueError(f"cited key_issue_ids not found: {sorted(str(i) for i in invented)}")
        return self


def build_imperatives(brand: Brand, key_issues: list[KeyIssue], *, run_record_repo=None) -> list[Imperative]:
    issues_summary = "\n".join(f"[{ki.id}] {ki.statement} (barrier: {ki.barrier})" for ki in key_issues)

    result = call(
        "imperatives",
        {"brand_name": brand.name, "key_issues_summary": issues_summary},
        _ImperativesDraftList,
        model_tier="standard",
        module="m5_imperatives",
        run_record_repo=run_record_repo,
        validation_context={"valid_key_issue_ids": {ki.id for ki in key_issues}},
        prompts_dir=PROMPTS_DIR,
    )
    return [
        Imperative(
            id=uuid4(),
            title=draft.title,
            key_issue_ids=draft.key_issue_ids,
            segment_id=draft.segment_id,
            from_rung=draft.from_rung,
            to_rung=draft.to_rung,
        )
        for draft in result.imperatives
    ]


# ---- 4. positioning (LLM; POD must be in whitespace) ----


class _PositioningDraft(BaseModel):
    target: str
    frame_of_reference: str
    point_of_difference: str
    driver: Driver
    reasons_to_believe: list[EvidencedText] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_driver_in_whitespace_and_evidence(self, info: ValidationInfo) -> "_PositioningDraft":
        context = info.context or {}
        whitespace_drivers = context.get("whitespace_drivers")
        if whitespace_drivers is not None and self.driver not in whitespace_drivers:
            raise ValueError(
                f"positioning driver '{self.driver.value}' is not in MessageMap.whitespace "
                f"({[d.value for d in whitespace_drivers]})"
            )
        valid_ids = context.get("valid_evidence_ids")
        if valid_ids is not None:
            cited = {i for r in self.reasons_to_believe for i in r.evidence_ids}
            invented = cited - set(valid_ids)
            if invented:
                raise ValueError(f"cited evidence_ids not found: {sorted(str(i) for i in invented)}")
        return self


def build_positioning(
    brand: Brand, message_map: MessageMap | None, evidence: list[Evidence], *, run_record_repo=None
) -> Positioning:
    # None means "no real constraint to enforce" — covers both no message_map
    # at all AND a message_map whose whitespace is genuinely empty (M4 found
    # no uncontested driver). Passing an empty *set* here instead would make
    # the validator below reject every possible driver, since nothing can
    # ever be "in" an empty set — that was the actual bug: M5 failed 100% of
    # the time whenever M4 found zero whitespace, not just sometimes.
    whitespace_drivers = {w.driver for w in message_map.whitespace} if message_map and message_map.whitespace else None
    whitespace_summary = (
        ", ".join(d.value for d in whitespace_drivers) if whitespace_drivers else "none identified"
    )

    draft = call(
        "positioning",
        {"brand_name": brand.name, "whitespace_summary": whitespace_summary},
        _PositioningDraft,
        model_tier="standard",
        module="m5_positioning",
        run_record_repo=run_record_repo,
        validation_context={
            "whitespace_drivers": whitespace_drivers,
            "valid_evidence_ids": _valid_evidence_ids(evidence),
        },
        prompts_dir=PROMPTS_DIR,
    )
    return Positioning(
        target=draft.target,
        frame_of_reference=draft.frame_of_reference,
        point_of_difference=draft.point_of_difference,
        driver=draft.driver,
        reasons_to_believe=draft.reasons_to_believe,
    )


# ---- 5. message_house (LLM) ----


class _MessageHouseDraft(BaseModel):
    core: str
    pillars: list[MessagePillar] = Field(min_length=3, max_length=3)
    by_persona: dict[UUID, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_pillars_and_evidence(self, info: ValidationInfo) -> "_MessageHouseDraft":
        context = info.context or {}
        persona_top3_by_driver = context.get("persona_top3_drivers")  # set[Driver]
        if persona_top3_by_driver is not None:
            for pillar in self.pillars:
                if pillar.driver not in persona_top3_by_driver:
                    raise ValueError(
                        f"pillar driver '{pillar.driver.value}' is not in any persona's top 3 drivers"
                    )
        valid_ids = context.get("valid_evidence_ids")
        if valid_ids is not None:
            cited = {i for p in self.pillars for i in p.proofs}
            invented = cited - set(valid_ids)
            if invented:
                raise ValueError(f"cited proof evidence_ids not found: {sorted(str(i) for i in invented)}")
        return self


def build_message_house(
    brand: Brand, personas: list[Persona], evidence: list[Evidence], *, run_record_repo=None
) -> MessageHouse:
    personas_summary = "\n".join(
        f"[{p.id}] {p.name}: top drivers = {[d.value for d in p.drivers_ranked[:3]]}, "
        f"share_of_potential={p.share_of_potential:.2f}"
        for p in personas
    ) or "none available"
    evidence_summary = "\n".join(f"[{e.id}] {e.claim}" for e in evidence[:100]) or "none available"

    persona_top3_drivers = {d for p in personas for d in p.drivers_ranked[:3]}

    draft = call(
        "message_house",
        {"brand_name": brand.name, "personas_summary": personas_summary, "evidence_summary": evidence_summary},
        _MessageHouseDraft,
        model_tier="standard",
        module="m5_message_house",
        run_record_repo=run_record_repo,
        validation_context={
            "persona_top3_drivers": persona_top3_drivers,
            "valid_evidence_ids": _valid_evidence_ids(evidence),
        },
        prompts_dir=PROMPTS_DIR,
    )
    return MessageHouse(core=draft.core, pillars=draft.pillars, by_persona=draft.by_persona)


# ---- 6. objectives (models/forecast.py sizes; LLM phrases the metric name) ----


class _ObjectiveLabel(BaseModel):
    imperative_id: UUID
    metric: str


class _ObjectiveLabelsList(BaseModel):
    labels: list[_ObjectiveLabel]


def word_objective_metrics(
    brand: Brand, imperatives: list[Imperative], *, run_record_repo=None
) -> dict[UUID, str]:
    """Only the metric NAME is an LLM call — baseline/target/due are sized
    deterministically by the caller (agents/m5/agent.py), per CLAUDE.md rule 1."""
    if not imperatives:
        return {}

    imperatives_summary = "\n".join(f"[{imp.id}] {imp.title} ({imp.from_rung.value}->{imp.to_rung.value})" for imp in imperatives)

    result = call(
        "objective_metrics",
        {"brand_name": brand.name, "imperatives_summary": imperatives_summary},
        _ObjectiveLabelsList,
        model_tier="standard",
        module="m5_objectives",
        run_record_repo=run_record_repo,
        validation_context={"valid_imperative_ids": {imp.id for imp in imperatives}},
        prompts_dir=PROMPTS_DIR,
    )
    return {label.imperative_id: label.metric for label in result.labels}


# ---- 7. strategies_tactics (LLM; channel refs filled after M6) ----


class _StrategyTacticDraft(BaseModel):
    imperative_id: UUID
    segments: list[UUID] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    content_needs: list[str] = Field(default_factory=list)


class _StrategiesTacticsDraftList(BaseModel):
    strategies: list[_StrategyTacticDraft]

    @model_validator(mode="after")
    def _check_imperative_ids(self, info: ValidationInfo) -> "_StrategiesTacticsDraftList":
        context = info.context or {}
        valid_ids = context.get("valid_imperative_ids")
        if valid_ids is not None:
            cited = {s.imperative_id for s in self.strategies}
            invented = cited - set(valid_ids)
            if invented:
                raise ValueError(f"cited imperative_ids not found: {sorted(str(i) for i in invented)}")
        return self


def build_strategies_tactics(
    brand: Brand, imperatives: list[Imperative], message_house: MessageHouse, *, run_record_repo=None
) -> list[StrategyTactic]:
    if not imperatives:
        return []

    imperatives_summary = "\n".join(f"[{imp.id}] {imp.title}" for imp in imperatives)

    result = call(
        "strategies_tactics",
        {"brand_name": brand.name, "imperatives_summary": imperatives_summary, "message_house_core": message_house.core},
        _StrategiesTacticsDraftList,
        model_tier="standard",
        module="m5_strategies_tactics",
        run_record_repo=run_record_repo,
        validation_context={"valid_imperative_ids": {imp.id for imp in imperatives}},
        prompts_dir=PROMPTS_DIR,
    )
    return [
        StrategyTactic(
            imperative_id=draft.imperative_id,
            segments=draft.segments,
            messages=draft.messages,
            channel_sequence_ref=None,  # filled in after M6
            content_needs=draft.content_needs,
        )
        for draft in result.strategies
    ]
