"""Deterministic segmentation/targeting math for M2 (specs/m2-segmentation.md).

Per CLAUDE.md rule 1, every score and threshold here is a tested pure
function — nothing in this module calls an LLM.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

import numpy as np

from schemas.base import ProvNumber
from schemas.enums import Access, Origin, Rung, Tier
from schemas.hcp import HCP, AdoptionState
from schemas.pack import Pack, PotentialProxies
from schemas.persona import Persona

NEUTRAL_WEIGHT = 1.0  # a category missing from the pack's weight dict is treated as average, not zero
MEASURED_CONFIDENCE_CAP = 0.5  # spec: estimate_potential's origin=estimated, confidence <= 0.5
NO_VOLUME_SIGNAL_CONFIDENCE = 0.2  # lower still when even the volume proxy is missing
UNKNOWN_RUNG_CONFIDENCE = 0.3  # spec: "unknown -> aware with confidence 0.3"


def estimate_potential(
    hcp: HCP, potential_proxies: PotentialProxies | None, as_of: date
) -> ProvNumber:
    """specs/m2-segmentation.md: 'linear score over proxies (specialty weight x
    setting weight x city-tier weight x patient-volume signal); origin=estimated,
    confidence <= 0.5.' The patient-volume signal supplies the absolute scale;
    the three category weights are 0-1 modifiers around it. A category not in
    the pack's weight dict is treated as neutral (1.0), not zero — we simply
    don't have a data-backed reason to penalize it."""
    potential_proxies = potential_proxies or PotentialProxies()
    specialty_w = potential_proxies.specialty_weight.get(hcp.specialty, NEUTRAL_WEIGHT)
    setting_w = potential_proxies.setting_weight.get(hcp.setting.value, NEUTRAL_WEIGHT)
    city_tier_w = (
        potential_proxies.city_tier_weight.get(hcp.geo.city_tier, NEUTRAL_WEIGHT)
        if hcp.geo.city_tier
        else NEUTRAL_WEIGHT
    )

    if hcp.patient_volume_estimate is not None:
        value = hcp.patient_volume_estimate * specialty_w * setting_w * city_tier_w
        confidence = MEASURED_CONFIDENCE_CAP
    else:
        # No volume anchor at all: the categorical product alone is a weak,
        # relative-only proxy, so we're less sure of it.
        value = specialty_w * setting_w * city_tier_w
        confidence = NO_VOLUME_SIGNAL_CONFIDENCE

    return ProvNumber(
        value=value,
        source="models.scores.estimate_potential",
        origin=Origin.estimated,
        as_of=as_of,
        confidence=confidence,
    )


def resolve_potential(
    hcp: HCP, potential_proxies: PotentialProxies | None, as_of: date
) -> ProvNumber:
    """potential_i = measured category volume, else estimate_potential(...)."""
    if hcp.potential.origin != Origin.estimated:
        return hcp.potential
    return estimate_potential(hcp, potential_proxies, as_of)


def assign_rung(hcp: HCP, brand_id: UUID, pack: Pack, entered_on: date) -> AdoptionState:
    """Fallback chain per specs/m2-segmentation.md: pack `rung_rules` (not
    defined by any pack today — this is a forward-compatible no-op until one
    exists), else rep-reported class (no pack maps rep_class -> rung today
    either, so this is also inert), else `unknown -> aware` @ 0.3 confidence.
    We do not invent a rep_class/rung mapping with no pack backing (CLAUDE.md
    rule 5)."""
    if pack.rung_rules:
        for rung_rule in pack.rung_rules:
            if _matches_rule(hcp, rung_rule.rule):
                rung = Rung(rung_rule.rung)
                return AdoptionState(
                    hcp_id=hcp.id,
                    brand_id=brand_id,
                    rung=rung,
                    entered_on=entered_on,
                    p_move_up=p_move_up(rung, pack),
                    measured=True,
                    rung_confidence=1.0,
                )

    rung = Rung.aware
    return AdoptionState(
        hcp_id=hcp.id,
        brand_id=brand_id,
        rung=rung,
        entered_on=entered_on,
        p_move_up=p_move_up(rung, pack),
        measured=False,
        rung_confidence=UNKNOWN_RUNG_CONFIDENCE,
    )


def _matches_rule(hcp: HCP, rule: dict[str, str]) -> bool:
    """Minimal equality-based predicate matcher for a future pack `rung_rules`
    entry, e.g. {"rep_class": "A"}. Unused by either shipped pack today."""
    return all(getattr(hcp, field, None) == expected for field, expected in rule.items())


def p_move_up(rung: Rung, pack: Pack, persona: Persona | None = None) -> float:
    """pack.priors.rung_transition_monthly[rung], adjusted by a persona
    multiplier if one is ever defined (Persona has no such field yet — this
    is a no-op hook until M3 adds one). A rung the pack's table doesn't cover
    (advocate/lapsed in both shipped packs) defaults to 0.0: there's nowhere
    further 'up' to move in this simple model."""
    base = pack.priors.rung_transition_monthly.get(rung.value, 0.0)
    return base  # persona multiplier hook: no-op until Persona defines one


def reachability(access: Access, pack: Pack, persona: Persona | None = None) -> float:
    """access_weight[access] * max_c(channel_affinity) — neutral (1.0) channel
    factor when no persona is available yet (spec: personas are optional
    pre-M3)."""
    access_w = pack.access_weights.get(access.value, NEUTRAL_WEIGHT)
    channel_factor = max(persona.channel_affinity.values()) if persona and persona.channel_affinity else NEUTRAL_WEIGHT
    return access_w * channel_factor


def opportunity(
    potential: float,
    target_share: float,
    current_share: float,
    p_move_up_value: float,
    reachability_value: float,
) -> float:
    """opportunity_i = potential_i * max(target_share - share_i, 0) * p_move_up * reachability_i."""
    share_gap = max(target_share - current_share, 0.0)
    return potential * share_gap * p_move_up_value * reachability_value


def percentile_rank(value: float, population: list[float]) -> float:
    """Where `value` falls in [0, 100] among `population`. Population of one
    (or empty) can't establish a percentile, so we treat it as the median."""
    if len(population) < 2:
        return 50.0
    return float((np.array(population) <= value).mean() * 100)


def assign_tier(
    potential_percentile: float,
    current_share: float,
    target_share: float,
    rung: Rung,
    reachability_value: float,
    pack: Pack,
) -> Tier:
    """The 4-rule table in specs/m2-segmentation.md, with thresholds read from
    pack.tiers (already part of the Pack schema since Foundations) rather than
    hard-coded — only the percentile computation itself (batch-relative) lives
    outside the pack."""
    t1 = pack.tiers.get("t1_grow")
    t2 = pack.tiers.get("t2_defend")
    t3 = pack.tiers.get("t3_develop")

    if (
        t1
        and t1.potential_pctl_min is not None
        and potential_percentile >= t1.potential_pctl_min
        and current_share < target_share
        and t1.rungs
        and rung.value in t1.rungs
    ):
        return Tier.t1_grow

    if (
        t2
        and t2.potential_pctl_min is not None
        and potential_percentile >= t2.potential_pctl_min
        and t2.rungs
        and rung.value in t2.rungs
    ):
        return Tier.t2_defend

    if (
        t3
        and t3.potential_pctl_min is not None
        and t3.potential_pctl_max is not None
        and t3.potential_pctl_min <= potential_percentile < t3.potential_pctl_max
        and t3.reachability_min is not None
        and reachability_value >= t3.reachability_min
    ):
        return Tier.t3_develop

    return Tier.t4_nurture


NEUTRAL_CONTENT_FIT = 0.5  # see models/scores.py::channel_fit docstring


def channel_fit(
    affinity: float,
    access: Access,
    stage_fit: float,
    pack: Pack,
    content_fit: float = NEUTRAL_CONTENT_FIT,
) -> float:
    """specs/m6-channel-mix.md: fit_i,c = w1*affinity + w2*access + w3*stage_fit
    + w4*content_fit, weights from pack.fit_weights (real pack data in both
    shipped packs). `content_fit[c][persona_i]` has no data source distinct
    from persona.channel_affinity (already used for `affinity` here) anywhere
    in this build, so it defaults to a neutral constant rather than double-
    counting the same signal or fabricating a second one — pass a real value
    once per-channel content-format data exists."""
    weights = pack.fit_weights
    access_w = pack.access_weights.get(access.value, NEUTRAL_WEIGHT)
    return (
        weights.get("affinity", 0.0) * affinity
        + weights.get("access", 0.0) * access_w
        + weights.get("stage_fit", 0.0) * stage_fit
        + weights.get("content_fit", 0.0) * content_fit
    )


def build_reason(
    potential: float,
    potential_percentile: float,
    current_share: float,
    target_share: float,
    rung: Rung,
    p_move_up_value: float,
    reachability_value: float,
    opportunity_value: float,
) -> str:
    """Human-readable sentence from the score components, per the Done-when
    requirement that every TargetList row explains itself."""
    return (
        f"Potential {potential:.1f} (P{potential_percentile:.0f} of the batch), "
        f"currently at {current_share:.1%} share vs {target_share:.1%} target, "
        f"rung={rung.value} (p(move up)={p_move_up_value:.2f}), "
        f"reachability={reachability_value:.2f} -> opportunity score {opportunity_value:.2f}."
    )
