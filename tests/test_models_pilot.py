import math
from dataclasses import dataclass

import pytest

from models.pilot import match_pairs, required_sample_size


@dataclass
class _Unit:
    name: str
    potential: float
    share: float
    rung_index: float


def test_match_pairs_pairs_the_closest_units_first():
    units = [
        _Unit("a", potential=100.0, share=0.1, rung_index=1),
        _Unit("b", potential=101.0, share=0.1, rung_index=1),  # near-identical to a
        _Unit("c", potential=900.0, share=0.5, rung_index=4),
        _Unit("d", potential=905.0, share=0.5, rung_index=4),  # near-identical to c
    ]
    pairs = match_pairs(units, lambda u: (u.potential, u.share, u.rung_index))
    assert len(pairs) == 2
    paired_names = {frozenset((p.a.name, p.b.name)) for p in pairs}
    assert frozenset({"a", "b"}) in paired_names
    assert frozenset({"c", "d"}) in paired_names


def test_match_pairs_handles_odd_count_by_leaving_one_unpaired():
    units = [_Unit(str(i), potential=float(i), share=0.1, rung_index=1) for i in range(5)]
    pairs = match_pairs(units, lambda u: (u.potential, u.share, u.rung_index))
    assert len(pairs) == 2  # 5 units -> 2 pairs, 1 left over


def test_match_pairs_returns_empty_for_fewer_than_two_units():
    assert match_pairs([_Unit("a", 1.0, 0.1, 1)], lambda u: (u.potential,)) == []
    assert match_pairs([], lambda u: (u.potential,)) == []


def test_required_sample_size_matches_hand_computed_value():
    # z_0.025 ~= 1.95996, z_0.8 ~= 0.84162 (power=0.8, alpha=0.05, the defaults)
    effect_size, std = 2.0, 5.0
    z_alpha, z_power = 1.9599639845400545, 0.8416212335729143
    expected = math.ceil(2 * (z_alpha + z_power) ** 2 * std**2 / effect_size**2)
    assert required_sample_size(effect_size, std) == expected


def test_required_sample_size_increases_with_smaller_effect_or_more_variance():
    baseline = required_sample_size(effect_size=2.0, std=5.0)
    smaller_effect = required_sample_size(effect_size=1.0, std=5.0)
    more_variance = required_sample_size(effect_size=2.0, std=10.0)
    assert smaller_effect > baseline
    assert more_variance > baseline


def test_required_sample_size_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        required_sample_size(effect_size=0.0, std=5.0)
    with pytest.raises(ValueError):
        required_sample_size(effect_size=2.0, std=-1.0)
