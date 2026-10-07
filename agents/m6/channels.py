"""The missing plumbing M6 needs: nothing before this module ever turned a
pack's raw channel list into real Channel entities. Two real gaps in both
shipped packs, both clearly flagged rather than silently guessed:

- unit_cost is `null` for every channel (pack.yaml's own comment:
  "TODO: loaded cost per call from client") — defaults to a placeholder
  (1.0/unit, confidence 0.2) so the fixture can still produce a complete,
  honestly-labelled-estimated plan.
- curve_prior.beta (the Hill curve's response ceiling) is also always null —
  defaults to 1.0, i.e. a normalized 0-1 response index, same placeholder
  treatment.

Field-force size (rep_count) isn't sourced anywhere either — passed in as an
optional parameter; rep_visit's capacity is None (uncapped) without it,
rather than a fabricated rep count.
"""

from __future__ import annotations

from datetime import date

from schemas.base import ProvMoney
from schemas.channel import Channel, ResponseCurve
from schemas.enums import CurveSource, Origin
from schemas.pack import Pack

PLACEHOLDER_UNIT_COST = 1.0
PLACEHOLDER_UNIT_COST_CONFIDENCE = 0.2
PLACEHOLDER_BETA = 1.0


def build_channels_from_pack(
    pack: Pack, rep_count: int | None = None, as_of: date | None = None
) -> list[Channel]:
    as_of = as_of or date.today()
    channels = []

    for pc in pack.channels:
        if pc.unit_cost is not None:
            unit_cost = ProvMoney(
                value=pc.unit_cost, source="pack", origin=Origin.internal, as_of=as_of, confidence=0.9,
                currency=pack.currency,
            )
        else:
            unit_cost = ProvMoney(
                value=PLACEHOLDER_UNIT_COST, source="placeholder: pack.yaml unit_cost is null",
                origin=Origin.estimated, as_of=as_of, confidence=PLACEHOLDER_UNIT_COST_CONFIDENCE,
                currency=pack.currency,
            )

        capacity = None
        if pc.capacity_rule and "reps" in pc.capacity_rule and rep_count is not None and pc.capacity_defaults:
            working_days = pc.capacity_defaults.get("working_days_per_month")
            calls_per_day = pc.capacity_defaults.get("calls_per_day")
            if working_days is not None and calls_per_day is not None:
                capacity = rep_count * working_days * calls_per_day

        compliance_rule_ids = [
            rule.id for rule in pack.compliance_rules if pc.id in rule.applies_to or "all" in rule.applies_to
        ]

        curve = ResponseCurve.model_validate(
            {
                "lambda": pc.curve_prior.lambda_,
                "alpha": pc.curve_prior.alpha,
                "gamma": pc.curve_prior.gamma,
                "beta": pc.curve_prior.beta if pc.curve_prior.beta is not None else PLACEHOLDER_BETA,
                "source": CurveSource.prior,
            }
        )

        channels.append(
            Channel(
                channel_ref=pc.id,
                name=pc.name,
                unit=pc.unit,
                unit_cost=unit_cost,
                capacity=capacity,
                stage_fit=pc.stage_fit,
                curve=curve,
                compliance_rule_ids=compliance_rule_ids,
            )
        )

    return channels
