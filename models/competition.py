"""Deterministic competitive-intelligence math for M4 (specs/m4-competitive.md).

Claim *tagging* (which Driver a claim is about) is an LLM judgment call; grid
strength, whitespace, parity risk, and ESOV are all aggregations over those
tags, computed here per CLAUDE.md rule 1.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas.competitive import CompetitorClaim, MessageGridCell, Whitespace
from schemas.enums import ClaimStrength, Driver
from schemas.persona import Persona

ESOV_FLAG_THRESHOLD = 5.0  # points; spec: "flag |esov| > 5 pts"


def build_grid(brand_claims: dict[str, list[CompetitorClaim]]) -> list[MessageGridCell]:
    """Dense drivers x brands matrix. Per specs/m4-competitive.md's own
    definitions: 0 brands claiming a driver -> absent for everyone; exactly 1
    -> owned for that brand; >=2 -> contested for each of them. Every other
    brand still gets an explicit `absent` cell for that driver."""
    brands_by_driver: dict[Driver, set[str]] = {d: set() for d in Driver}
    for brand, claims in brand_claims.items():
        for claim in claims:
            brands_by_driver[claim.driver].add(brand)

    cells: list[MessageGridCell] = []
    for driver in Driver:
        claiming_brands = brands_by_driver[driver]
        for brand in brand_claims:
            if brand not in claiming_brands:
                strength = ClaimStrength.absent
            elif len(claiming_brands) == 1:
                strength = ClaimStrength.owned
            else:
                strength = ClaimStrength.contested
            cells.append(MessageGridCell(driver=driver, brand=brand, strength=strength))

    return cells


def compute_driver_importance(personas: list[Persona]) -> dict[Driver, float]:
    """Persona-weighted driver importance: driver_vector per persona, weighted
    mean by share_of_potential. Reuses models/personas.py rather than
    duplicating the rank-weighting logic."""
    from models.personas import DRIVER_ORDER, driver_vector

    importance = {d: 0.0 for d in Driver}
    if not personas:
        return importance

    total_weight = sum(p.share_of_potential for p in personas)
    if total_weight <= 0:
        return importance

    for persona in personas:
        vector = driver_vector(persona.drivers_ranked)
        weight = persona.share_of_potential / total_weight
        for i, driver in enumerate(DRIVER_ORDER):
            importance[driver] += vector[i] * weight

    return importance


def _top_drivers(importance: dict[Driver, float], top_n: int) -> list[Driver]:
    return sorted(importance, key=lambda d: importance[d], reverse=True)[:top_n]


def find_whitespace(
    grid: list[MessageGridCell],
    importance: dict[Driver, float],
    personas: list[Persona],
    top_n: int = 4,
) -> list[Whitespace]:
    """specs/m4-competitive.md: driver d is whitespace if importance(d) is in
    the top `top_n` AND no brand has `owned` for d."""
    owned_drivers = {cell.driver for cell in grid if cell.strength == ClaimStrength.owned}

    whitespace = []
    for driver in _top_drivers(importance, top_n):
        if driver in owned_drivers:
            continue
        caring_personas = sorted(
            (p for p in personas if driver in p.drivers_ranked[:3]),
            key=lambda p: p.share_of_potential,
            reverse=True,
        )
        whitespace.append(
            Whitespace(
                driver=driver,
                personas=[p.name for p in caring_personas],
                rationale=(
                    f"{driver.value} ranks in the top {top_n} drivers by persona-weighted "
                    f"importance ({importance[driver]:.2f}) and no brand currently owns it."
                ),
            )
        )
    return whitespace


def find_parity_risks(
    grid: list[MessageGridCell], importance: dict[Driver, float], our_brand: str, top_n: int = 4
) -> list[str]:
    """Not explicitly formulaic in the spec — the natural analog of whitespace
    on the other side: top-importance drivers a COMPETITOR (not us) owns,
    meaning we risk losing ground on something patients/prescribers value."""
    owned_by_others = {
        cell.driver for cell in grid if cell.strength == ClaimStrength.owned and cell.brand != our_brand
    }
    owning_brand = {
        cell.driver: cell.brand
        for cell in grid
        if cell.strength == ClaimStrength.owned and cell.brand != our_brand
    }

    risks = []
    for driver in _top_drivers(importance, top_n):
        if driver in owned_by_others:
            risks.append(
                f"{owning_brand[driver]} owns {driver.value}, a top-{top_n} importance driver "
                f"we do not currently own."
            )
    return risks


@dataclass
class ESOVResult:
    brand: str
    period: str
    sov: float
    som: float
    esov: float
    flagged: bool


def compute_esov(
    sov_by_brand_period: dict[tuple[str, str], float],
    som_by_brand_period: dict[tuple[str, str], float],
) -> list[ESOVResult]:
    """esov_b = sov_b - som_b per period, flagged when |esov| > 5 pts. Only
    computed for (brand, period) pairs present in BOTH inputs — per spec,
    callers skip this entirely (with a note) when neither CSV is provided."""
    results = []
    for brand, period in sorted(set(sov_by_brand_period) & set(som_by_brand_period)):
        sov = sov_by_brand_period[(brand, period)]
        som = som_by_brand_period[(brand, period)]
        esov = sov - som
        results.append(
            ESOVResult(
                brand=brand,
                period=period,
                sov=sov,
                som=som,
                esov=esov,
                flagged=abs(esov) > ESOV_FLAG_THRESHOLD,
            )
        )
    return results
