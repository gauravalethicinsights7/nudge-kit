"""Deterministic persona math for M3 (specs/m3-personas.md): share
normalization and distinctness. Per CLAUDE.md rule 1, the LLM only proposes
relative weights/rankings — this is where the actual arithmetic lives.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

from schemas.enums import Driver
from schemas.persona import Persona

DRIVER_ORDER = list(Driver)  # fixed order, so vectors are comparable across personas


def normalize_shares(raw_weights: list[float]) -> list[float]:
    """Proportional normalization so the result sums to exactly 1.0 (the
    spec's +/-0.02 tolerance is a floor, not a target). All-zero/empty input
    falls back to an equal split rather than dividing by zero."""
    n = len(raw_weights)
    if n == 0:
        return []
    total = sum(raw_weights)
    if total <= 0:
        return [1.0 / n] * n
    return [w / total for w in raw_weights]


def driver_vector(drivers_ranked: list[Driver]) -> np.ndarray:
    """Rank-weighted vector over the full Driver enum: the top-ranked driver
    gets the highest weight, so cosine similarity reflects rank agreement,
    not just set overlap. Fixed length/order across all personas."""
    n = len(DRIVER_ORDER)
    rank_of = {driver: i for i, driver in enumerate(drivers_ranked)}
    return np.array([n - rank_of.get(driver, n) for driver in DRIVER_ORDER], dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def pairwise_distinctness(
    personas: list[Persona], threshold: float = 0.85
) -> list[tuple[str, str, float]]:
    """Returns (name_a, name_b, similarity) for every pair AT OR ABOVE
    threshold — i.e. the violations of specs/m3-personas.md's 'pairwise
    cosine similarity of persona driver vectors < 0.85.'"""
    vectors = {p.id: driver_vector(p.drivers_ranked) for p in personas}
    return [
        (a.name, b.name, sim)
        for a, b in combinations(personas, 2)
        if (sim := cosine_similarity(vectors[a.id], vectors[b.id])) >= threshold
    ]
