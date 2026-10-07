"""Pilot design helper for M8 (specs/m8-measurement.md): 'matched pairs by
potential, share, rung mix; power calc for target effect.'
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, TypeVar

import numpy as np
from scipy.stats import norm

T = TypeVar("T")


@dataclass
class MatchedPair:
    a: object
    b: object
    distance: float


def match_pairs(units: list[T], feature_fn: Callable[[T], tuple[float, ...]]) -> list[MatchedPair]:
    """Greedy nearest-neighbour matching on a normalized feature vector
    (potential, share, rung mix, ...) — pairs the two closest remaining units
    repeatedly until fewer than 2 units remain. Features are min-max
    normalized first so no single feature (e.g. potential, often orders of
    magnitude larger than a rung index) dominates the distance."""
    if len(units) < 2:
        return []

    raw_features = np.array([feature_fn(u) for u in units], dtype=float)
    mins, maxs = raw_features.min(axis=0), raw_features.max(axis=0)
    ranges = np.where(maxs > mins, maxs - mins, 1.0)
    normalized = (raw_features - mins) / ranges

    remaining = list(range(len(units)))
    pairs: list[MatchedPair] = []
    while len(remaining) >= 2:
        i = remaining[0]
        best_j, best_dist = None, math.inf
        for j in remaining[1:]:
            dist = float(np.linalg.norm(normalized[i] - normalized[j]))
            if dist < best_dist:
                best_j, best_dist = j, dist
        pairs.append(MatchedPair(a=units[i], b=units[best_j], distance=best_dist))
        remaining.remove(i)
        remaining.remove(best_j)
    return pairs


def required_sample_size(effect_size: float, std: float, power: float = 0.8, alpha: float = 0.05) -> int:
    """Standard two-sample z-test sample-size formula (per arm):
    n = 2 * (z_alpha/2 + z_power)^2 * std^2 / effect_size^2."""
    if effect_size <= 0:
        raise ValueError(f"effect_size must be > 0, got {effect_size}")
    if std < 0:
        raise ValueError(f"std must be >= 0, got {std}")
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)
    n = 2 * (z_alpha + z_power) ** 2 * std**2 / effect_size**2
    return math.ceil(n)
