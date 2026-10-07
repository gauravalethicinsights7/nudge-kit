"""Deterministic brand-plan math for M5 (specs/m5-brand-plan.md): the
revenue-at-stake ranking behind key issues, the compliance guardrail
(CLAUDE.md rule 6: "compliance guardrails run before any output leaves
M5/M7"), and the mechanical human-review checklist. Per CLAUDE.md rule 1, the
LLM only words these sections — the ranking and the compliance check are
pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from schemas.base import ProvMoney
from schemas.brand_plan import BrandPlan, ComplianceFlag
from schemas.enums import Origin
from schemas.hcp import Segment
from schemas.pack import Pack

TARGET_KEY_ISSUE_COUNT = 6  # spec: "(4-6)" — a target, not a hard schema minimum; see schemas/brand_plan.py


def revenue_at_stake(segment: Segment, net_price: float, currency: str, as_of: date | None = None) -> ProvMoney:
    """revenue_at_stake(issue) = segment.total_potential * (target_share - avg_share) * net_price."""
    as_of = as_of or date.today()
    share_gap = max(segment.target_share - segment.avg_share, 0.0)
    value = segment.total_potential * share_gap * net_price
    return ProvMoney(
        value=value,
        source="models.plan.revenue_at_stake",
        origin=Origin.estimated,
        as_of=as_of,
        confidence=0.5,
        currency=currency,
    )


@dataclass
class KeyIssueCandidate:
    segment: Segment
    revenue_at_stake: ProvMoney


def rank_key_issues(
    segments: list[Segment], net_price: float, currency: str, top_n: int = TARGET_KEY_ISSUE_COUNT
) -> list[KeyIssueCandidate]:
    """Ranks segments by revenue_at_stake, highest first, for the LLM to word
    into key issue statements. Returns however many segments exist, up to
    top_n — never pads with fabricated issues."""
    candidates = [
        KeyIssueCandidate(segment=s, revenue_at_stake=revenue_at_stake(s, net_price, currency)) for s in segments
    ]
    candidates.sort(key=lambda c: c.revenue_at_stake.value, reverse=True)
    return candidates[:top_n]


# Curated, deliberately narrow trigger phrases per compliance-rule concept.
# Extracting keywords generically from a rule's own prose (e.g. IN-REMIND-01
# mentions "educational" and "professional") would false-positive on entirely
# ordinary brand-plan language — a plan legitimately discussing "educational
# content" isn't thereby violating an item-cost-cap rule. These phrases are a
# universal way to detect the *concept* each rule guards against (unsubstan-
# tiated superlative claims, gifts, off-label promotion, DTC of a Rx-only
# drug) — genuinely code-side detection logic, not a market fact, so this
# doesn't violate CLAUDE.md rule 5 the way hard-coding a channel or a
# benchmark would. Rule IDs not listed here simply can't be mechanically
# checked yet — they still need a human, which is exactly why this is a
# "flag for review," not a substitute for real legal/MLR sign-off.
RULE_TRIGGER_PHRASES: dict[str, list[str]] = {
    "IN-GIFT-01": ["gift", "cash payment", "pecuniary benefit", "complimentary trip"],
    "IN-CLAIM-01": [
        "guaranteed",
        "guarantee",
        "cure",
        "completely safe",
        "zero risk",
        "zero side effects",
        "superior to",
        "#1",
        "best-in-class",
        "proven best",
        "no side effects",
    ],
    "IN-DTC-01": ["direct to consumer", "public awareness campaign", "patient advertising"],
    "US-FB-01": ["guaranteed", "completely safe", "risk-free", "no side effects"],
    "US-LABEL-01": ["off-label", "unapproved use"],
    "US-PHRMA-01": ["gift", "entertainment", "recreational"],
}


def check_compliance(plan: BrandPlan, pack: Pack) -> list[ComplianceFlag]:
    """The compliance guardrail (CLAUDE.md rule 6: 'compliance guardrails run
    before any output leaves M5'). A real legal/MLR review is out of scope —
    this is the mechanical floor: a curated phrase match per rule concept
    against the plan's own claim-bearing text, flagged for human attention
    rather than silently blocking the plan."""
    text_blobs = [
        plan.situation.summary,
        plan.positioning.target,
        plan.positioning.frame_of_reference,
        plan.positioning.point_of_difference,
        plan.message_house.core,
        *(ki.statement for ki in plan.key_issues),
        *(imp.title for imp in plan.imperatives),
        *(p.message for p in plan.message_house.pillars),
        *(st for s in plan.strategies_tactics for st in s.messages),
    ]
    full_text = " ".join(text_blobs).lower()

    flags = []
    for rule in pack.compliance_rules:
        triggers = RULE_TRIGGER_PHRASES.get(rule.id, [])
        if any(phrase in full_text for phrase in triggers):
            flags.append(ComplianceFlag(item=rule.rule, rule_id=rule.id, severity=rule.severity))

    return flags


def build_review_checklist(plan: BrandPlan) -> list[str]:
    """Mechanical enumeration of every item needing human sign-off — spec's
    'human review template generated (checklist of items to approve)'."""
    items = [
        "Approve situation summary",
        *[f"Approve key issue: {ki.statement}" for ki in plan.key_issues],
        *[f"Approve imperative: {imp.title}" for imp in plan.imperatives],
        "Approve positioning (target / frame of reference / point of difference)",
        "Approve message house core idea",
        *[f"Approve message pillar ({p.driver.value}): {p.message}" for p in plan.message_house.pillars],
        *[f"Approve objective: {o.metric} ({o.baseline} -> {o.target} by {o.due})" for o in plan.objectives],
        "Approve base/upside/downside forecast and its assumptions",
        *[f"Resolve compliance flag ({f.severity}): {f.item}" for f in plan.compliance_flags],
    ]
    return items
