"""M6 orchestrator: build channels from the pack, score fit per segment
(x its best-matched persona), fit response curves (priors, since the fixture
has no history), optimise the mix per segment, build ChannelPlan, and fill in
BrandPlan.budget (M5 left it as an explicit placeholder). No LLM calls
anywhere in this module — fully deterministic/quantitative, like M2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from agents.m6.channels import build_channels_from_pack
from models.optimiser import optimise_mix
from models.scores import channel_fit as compute_channel_fit
from schemas.base import ProvMoney
from schemas.brand import Brand
from schemas.brand_plan import Budget, BudgetLine
from schemas.channel import Channel
from schemas.channel_fit import ChannelFit, FitComponents
from schemas.channel_plan import ChannelAllocation, ChannelPlan
from schemas.enums import Access, Origin, Rung
from schemas.hcp import Segment
from schemas.pack import Pack
from schemas.persona import Persona
from store.brand_plan_repo import BrandPlanRepo
from store.channel_fit_repo import ChannelFitRepo
from store.channel_plan_repo import ChannelPlanRepo
from store.channel_repo import ChannelRepo

# No segment<->persona link exists anywhere in this build (M2 and M3 are
# independent axes per CLAUDE.md's spine) and Segment carries no rung/access
# data of its own (that's HCP/AdoptionState-level, and HCP[] is optional per
# spec) — both documented simplifications, not silent guesses.
NEUTRAL_ACCESS = Access.unknown
NEUTRAL_STAGE_FIT = 0.5


@dataclass
class M6Result:
    channels: list[Channel]
    channel_fits: list[ChannelFit]
    channel_plan: ChannelPlan
    # Always populated, even when no upstream BrandPlan exists yet to receive
    # them via update_budget() below — marginal ROI/position per channel is a
    # first-class M6 output (specs/m6-channel-mix.md), not just a side effect
    # of mutating M5's plan.
    budget_lines: list[BudgetLine]


def _representative_persona(personas: list[Persona]) -> Persona | None:
    return max(personas, key=lambda p: p.share_of_potential, default=None)


def _segment_stage_fit(channel: Channel, segment: Segment, pack: Pack) -> float:
    tier_rule = pack.tiers.get(segment.tier.value)
    rungs = tier_rule.rungs if tier_rule and tier_rule.rungs else None
    if not rungs:
        return NEUTRAL_STAGE_FIT
    values = [channel.stage_fit.get(Rung(r), NEUTRAL_STAGE_FIT) for r in rungs]
    return sum(values) / len(values)


def run(
    brand: Brand,
    pack: Pack,
    session: Session,
    segments: list[Segment],
    personas: list[Persona],
    budget_envelope: float,
    rep_count: int | None = None,
    as_of: date | None = None,
) -> M6Result:
    as_of = as_of or date.today()
    channels = build_channels_from_pack(pack, rep_count=rep_count, as_of=as_of)
    saved_channels = ChannelRepo(session).add_many(brand.id, channels)

    persona = _representative_persona(personas)
    total_potential = sum(s.total_potential for s in segments) or 1.0

    channel_fits: list[ChannelFit] = []
    allocations: dict[UUID, dict[str, ChannelAllocation]] = {}
    budget_lines: list[BudgetLine] = []

    for segment in segments:
        fit_scores: dict[str, float] = {}
        for channel in saved_channels:
            affinity = persona.channel_affinity.get(channel.channel_ref, 0.5) if persona else 0.5
            stage_fit_value = _segment_stage_fit(channel, segment, pack)
            score = compute_channel_fit(affinity, NEUTRAL_ACCESS, stage_fit_value, pack)
            fit_scores[channel.channel_ref] = score
            channel_fits.append(
                ChannelFit(
                    brand_id=brand.id,
                    segment_id=segment.id,
                    persona_id=persona.id if persona else None,
                    channel_id=channel.channel_ref,
                    fit_score=max(0.0, min(1.0, score)),
                    components=FitComponents(
                        affinity=affinity,
                        access=pack.access_weights.get(NEUTRAL_ACCESS.value, 0.5),
                        stage_fit=stage_fit_value,
                        content_fit=0.5,
                    ),
                )
            )

        segment_budget = budget_envelope * (segment.total_potential / total_potential)
        results = optimise_mix(
            saved_channels,
            fit_scores,
            budget=segment_budget,
            hcp_count=max(segment.hcp_count, 1),
            freq_caps=pack.frequency_caps,
            compliance_allowed=None,  # see agents/m6/agent.py module note: no pack rule maps to an outright ban today
        )

        allocations[segment.id] = {}
        for result in results:
            channel = next(c for c in saved_channels if c.channel_ref == result.channel_id)
            currency = channel.unit_cost.currency if channel.unit_cost else pack.currency
            spend_origin = channel.unit_cost.origin if channel.unit_cost else Origin.estimated
            spend_confidence = channel.unit_cost.confidence if channel.unit_cost else 0.2
            spend_amount = ProvMoney(
                value=result.spend,
                source="models.optimiser.optimise_mix",
                origin=spend_origin,
                as_of=as_of,
                confidence=spend_confidence,
                currency=currency,
            )

            allocations[segment.id][result.channel_id] = ChannelAllocation(
                touches_per_month=result.activity,
                spend=spend_amount,
                share_of_budget=(result.spend / segment_budget) if segment_budget > 0 else 0.0,
            )
            budget_lines.append(
                BudgetLine(
                    imperative_id=None,
                    channel_id=result.channel_id,
                    amount=spend_amount,
                    marginal_roi=result.marginal_roi,
                    position=result.position,
                )
            )

    channel_plan = ChannelPlan(brand_id=brand.id, allocations=allocations)
    saved_channel_fits = ChannelFitRepo(session).add_many(channel_fits)
    saved_channel_plan = ChannelPlanRepo(session).add(channel_plan)

    existing_plan = BrandPlanRepo(session).get_latest_for_brand(brand.id)
    if existing_plan is not None:
        BrandPlanRepo(session).update_budget(
            existing_plan.id, Budget(lines=budget_lines, placeholder=False)
        )

    return M6Result(
        channels=saved_channels,
        channel_fits=saved_channel_fits,
        channel_plan=saved_channel_plan,
        budget_lines=budget_lines,
    )
