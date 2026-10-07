import pytest

from models.personas import (
    cosine_similarity,
    driver_vector,
    normalize_shares,
    pairwise_distinctness,
)
from schemas.enums import Driver
from tests.factories import make_persona


def test_normalize_shares_sums_to_one():
    shares = normalize_shares([10.0, 20.0, 30.0, 40.0])
    assert sum(shares) == pytest.approx(1.0)
    assert shares == [pytest.approx(0.1), pytest.approx(0.2), pytest.approx(0.3), pytest.approx(0.4)]


def test_normalize_shares_handles_all_zero_with_equal_split():
    shares = normalize_shares([0.0, 0.0, 0.0, 0.0])
    assert shares == [0.25, 0.25, 0.25, 0.25]


def test_normalize_shares_empty_input():
    assert normalize_shares([]) == []


def test_driver_vector_top_ranked_gets_highest_weight():
    ranked = list(Driver)  # first element is top-ranked
    vector = driver_vector(ranked)
    top_index = list(Driver).index(ranked[0])
    last_index = list(Driver).index(ranked[-1])
    assert vector[top_index] > vector[last_index]


def test_driver_vector_fixed_length():
    vector = driver_vector([Driver.cost])
    assert len(vector) == len(list(Driver))


def test_cosine_similarity_identical_vectors_is_one():
    v = driver_vector(list(Driver))
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_zero_vector_is_zero():
    import numpy as np

    assert cosine_similarity(np.zeros(3), np.array([1.0, 2.0, 3.0])) == 0.0


def test_pairwise_distinctness_flags_near_identical_driver_rankings():
    order = list(Driver)
    reversed_order = list(reversed(order))

    p1 = make_persona()
    p1.name = "Persona A"
    p1.drivers_ranked = order
    p2 = make_persona()
    p2.name = "Persona B"
    p2.drivers_ranked = order  # identical ranking -> similarity 1.0
    p3 = make_persona()
    p3.name = "Persona C"
    p3.drivers_ranked = reversed_order  # maximally different ranking

    violations = pairwise_distinctness([p1, p2, p3], threshold=0.85)
    violating_pairs = {(v[0], v[1]) for v in violations} | {(v[1], v[0]) for v in violations}

    assert (p1.name, p2.name) in violating_pairs or (p2.name, p1.name) in violating_pairs
    assert (p1.name, p3.name) not in violating_pairs
