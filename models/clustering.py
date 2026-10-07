"""Deterministic clustering primitive for M3 (specs/m3-personas.md).

Used correctly as-is for call_notes/social (numeric embeddings — KMeans is
the right tool for that). Used as a documented stand-in for survey's raw
categorical items (encoded to numeric first) until a real survey pipeline
swaps in true k-prototypes — that would only touch agents/m3/survey.py, not
this function. Per CLAUDE.md rule 1, only this deterministic math clusters;
the LLM names/describes clusters afterward.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


@dataclass
class ClusteringResult:
    k: int
    labels: list[int]  # cluster index per input vector, same order as input
    cluster_sizes: dict[int, int]
    silhouette: float


def cluster_vectors(
    vectors: list[list[float]], k_min: int = 4, k_max: int = 6, seed: int = 42
) -> ClusteringResult:
    """KMeans across k in [k_min, k_max], picks the k with the best silhouette
    score. Needs at least k_min + 1 points (silhouette requires k <= n - 1)."""
    n = len(vectors)
    if n < k_min + 1:
        raise ValueError(f"need at least {k_min + 1} vectors to try k>={k_min} clusters, got {n}")

    x = np.array(vectors)
    best: tuple[int, float, np.ndarray] | None = None

    for k in range(k_min, min(k_max, n - 1) + 1):
        model = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labels = model.fit_predict(x)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(x, labels)
        if best is None or score > best[1]:
            best = (k, score, labels)

    if best is None:
        # Degenerate input (e.g. near-identical vectors): silhouette couldn't
        # discriminate any k. Fall back to k_min rather than raising.
        model = KMeans(n_clusters=k_min, random_state=seed, n_init=10)
        labels = model.fit_predict(x)
        best = (k_min, float("nan"), labels)

    k, score, labels = best
    sizes = {int(c): int((labels == c).sum()) for c in set(labels)}
    return ClusteringResult(
        k=k, labels=[int(label) for label in labels], cluster_sizes=sizes, silhouette=float(score)
    )
