from uuid import uuid4

import pytest

from models.competition import build_grid, compute_esov, find_parity_risks, find_whitespace
from schemas.competitive import CompetitorClaim, MessageGridCell
from schemas.enums import ClaimStrength, Driver, PersonaDerivation
from schemas.persona import Persona


def _claim(driver: Driver) -> CompetitorClaim:
    return CompetitorClaim(driver=driver, text="claim", strength=ClaimStrength.absent, evidence_id=uuid4())


def _full_ranking(*top: Driver) -> list[Driver]:
    """A full Driver permutation with `top` first, in order, then the rest."""
    rest = [d for d in Driver if d not in top]
    return list(top) + rest


def _persona(name: str, top_drivers: list[Driver], share_of_potential: float) -> Persona:
    return Persona(
        brand_id=uuid4(),
        name=name,
        drivers_ranked=_full_ranking(*top_drivers),
        barriers_by_rung={"aware": ["x"], "considering": ["x"], "trialist": ["x"]},
        share_of_universe=share_of_potential,
        share_of_potential=share_of_potential,
        derivation=PersonaDerivation.synthetic,
        assumption=True,
    )


# ---- build_grid ----


def test_build_grid_single_claimant_is_owned():
    grid = build_grid({"BrandA": [_claim(Driver.cost)], "BrandB": []})
    cell = next(c for c in grid if c.driver == Driver.cost and c.brand == "BrandA")
    assert cell.strength == ClaimStrength.owned
    other = next(c for c in grid if c.driver == Driver.cost and c.brand == "BrandB")
    assert other.strength == ClaimStrength.absent


def test_build_grid_multiple_claimants_are_contested():
    grid = build_grid({"BrandA": [_claim(Driver.efficacy)], "BrandB": [_claim(Driver.efficacy)]})
    cells = [c for c in grid if c.driver == Driver.efficacy]
    assert all(c.strength == ClaimStrength.contested for c in cells)


def test_build_grid_no_claimants_is_absent_for_everyone():
    grid = build_grid({"BrandA": [], "BrandB": []})
    cells = [c for c in grid if c.driver == Driver.safety]
    assert all(c.strength == ClaimStrength.absent for c in cells)


def test_build_grid_is_dense_every_driver_every_brand():
    grid = build_grid({"BrandA": [_claim(Driver.cost)], "BrandB": []})
    assert len(grid) == len(list(Driver)) * 2


# ---- find_whitespace (specs/m4-competitive.md's explicit Done-when item) ----


def test_find_whitespace_flags_high_importance_unclaimed_driver():
    personas = [
        _persona("P1", [Driver.support_services, Driver.evidence_strength, Driver.cost], 0.3),
        _persona("P2", [Driver.cost, Driver.support_services, Driver.efficacy], 0.3),
        _persona("P3", [Driver.evidence_strength, Driver.cost, Driver.support_services], 0.2),
        _persona("P4", [Driver.tolerability, Driver.convenience, Driver.efficacy], 0.2),
    ]
    grid = [
        MessageGridCell(driver=Driver.cost, brand="BrandA", strength=ClaimStrength.owned),
        MessageGridCell(driver=Driver.evidence_strength, brand="BrandB", strength=ClaimStrength.owned),
        MessageGridCell(driver=Driver.efficacy, brand="BrandA", strength=ClaimStrength.contested),
        MessageGridCell(driver=Driver.efficacy, brand="BrandB", strength=ClaimStrength.contested),
        MessageGridCell(driver=Driver.support_services, brand="BrandA", strength=ClaimStrength.absent),
        MessageGridCell(driver=Driver.support_services, brand="BrandB", strength=ClaimStrength.absent),
    ]
    from models.competition import compute_driver_importance

    importance = compute_driver_importance(personas)
    whitespace = find_whitespace(grid, importance, personas, top_n=4)

    whitespace_drivers = {w.driver for w in whitespace}
    assert Driver.support_services in whitespace_drivers
    assert Driver.cost not in whitespace_drivers  # owned by BrandA
    assert Driver.evidence_strength not in whitespace_drivers  # owned by BrandB


def test_find_whitespace_excludes_owned_driver_even_if_top_importance():
    personas = [_persona("P1", [Driver.cost], 1.0)]
    grid = [MessageGridCell(driver=Driver.cost, brand="BrandA", strength=ClaimStrength.owned)]
    from models.competition import compute_driver_importance

    importance = compute_driver_importance(personas)
    whitespace = find_whitespace(grid, importance, personas, top_n=1)
    assert whitespace == []


# ---- find_parity_risks ----


def test_find_parity_risks_flags_competitor_owned_top_driver():
    personas = [_persona("P1", [Driver.efficacy], 1.0)]
    grid = [MessageGridCell(driver=Driver.efficacy, brand="Competitor X", strength=ClaimStrength.owned)]
    from models.competition import compute_driver_importance

    importance = compute_driver_importance(personas)
    risks = find_parity_risks(grid, importance, our_brand="Brand S", top_n=1)
    assert any("Competitor X" in r and "efficacy" in r for r in risks)


def test_find_parity_risks_ignores_our_own_ownership():
    personas = [_persona("P1", [Driver.efficacy], 1.0)]
    grid = [MessageGridCell(driver=Driver.efficacy, brand="Brand S", strength=ClaimStrength.owned)]
    from models.competition import compute_driver_importance

    importance = compute_driver_importance(personas)
    risks = find_parity_risks(grid, importance, our_brand="Brand S", top_n=1)
    assert risks == []


# ---- compute_esov ----


def test_compute_esov_flags_gap_over_five_points():
    results = compute_esov({("BrandA", "2026-01"): 20.0}, {("BrandA", "2026-01"): 10.0})
    assert len(results) == 1
    assert results[0].esov == pytest.approx(10.0)
    assert results[0].flagged is True


def test_compute_esov_does_not_flag_small_gap():
    results = compute_esov({("BrandA", "2026-01"): 12.0}, {("BrandA", "2026-01"): 10.0})
    assert results[0].flagged is False


def test_compute_esov_only_covers_periods_in_both_inputs():
    results = compute_esov(
        {("BrandA", "2026-01"): 20.0, ("BrandB", "2026-01"): 5.0},
        {("BrandA", "2026-01"): 10.0},
    )
    assert len(results) == 1
    assert results[0].brand == "BrandA"
