import numpy as np
import pytest

from models.clustering import cluster_vectors


def _well_separated_clusters(k: int, per_cluster: int = 10, dim: int = 5, spread: float = 0.1) -> list[list[float]]:
    rng = np.random.default_rng(0)
    vectors = []
    for i in range(k):
        center = np.zeros(dim)
        center[i % dim] = 10.0 * (i + 1)
        for _ in range(per_cluster):
            vectors.append((center + rng.normal(scale=spread, size=dim)).tolist())
    return vectors


def test_cluster_vectors_recovers_correct_k_for_well_separated_data():
    vectors = _well_separated_clusters(k=4)
    result = cluster_vectors(vectors, k_min=4, k_max=6)
    assert result.k == 4
    assert len(result.labels) == len(vectors)
    assert sum(result.cluster_sizes.values()) == len(vectors)
    assert result.silhouette > 0.8


def test_cluster_vectors_groups_same_cluster_members_together():
    vectors = _well_separated_clusters(k=4, per_cluster=10)
    result = cluster_vectors(vectors, k_min=4, k_max=6)
    # first 10 vectors all belong to the same source cluster
    labels_for_first_group = result.labels[:10]
    assert len(set(labels_for_first_group)) == 1


def test_cluster_vectors_raises_when_too_few_points():
    with pytest.raises(ValueError):
        cluster_vectors([[1.0], [2.0], [3.0]], k_min=4, k_max=6)


def test_cluster_vectors_falls_back_gracefully_on_degenerate_input():
    # all identical points: silhouette can't discriminate any k
    vectors = [[1.0, 1.0]] * 8
    result = cluster_vectors(vectors, k_min=4, k_max=6)
    assert result.k == 4
    assert len(result.labels) == 8
