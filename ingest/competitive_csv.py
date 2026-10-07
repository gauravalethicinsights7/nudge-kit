"""CSV -> SOM/SOV ingest for M4's optional ESOV inputs
(specs/m4-competitive.md: 'share audit CSV (brand x period x share)',
'SOV / promo audit CSV (brand x channel x period x activity)'). Both are
optional; models/competition.py::compute_esov only computes for (brand,
period) pairs present in both — ESOV is skipped with a note when neither is
supplied.
"""

from __future__ import annotations

from pathlib import Path

from ingest.csv_utils import read_csv_skipping_comments


def load_share_audit_csv(path: Path | str) -> dict[tuple[str, str], float]:
    """brand, period, share -> {(brand, period): share} — this is SOM."""
    df = read_csv_skipping_comments(Path(path))
    return {(str(row["brand"]), str(row["period"])): float(row["share"]) for _, row in df.iterrows()}


def load_promo_audit_csv(path: Path | str) -> dict[tuple[str, str], float]:
    """brand, channel, period, activity -> {(brand, period): sov}, where SOV
    is that brand's share of total activity across all brands in that period."""
    df = read_csv_skipping_comments(Path(path))

    activity_by_brand_period: dict[tuple[str, str], float] = {}
    total_by_period: dict[str, float] = {}
    for _, row in df.iterrows():
        brand, period, activity = str(row["brand"]), str(row["period"]), float(row["activity"])
        key = (brand, period)
        activity_by_brand_period[key] = activity_by_brand_period.get(key, 0.0) + activity
        total_by_period[period] = total_by_period.get(period, 0.0) + activity

    return {
        (brand, period): (activity / total_by_period[period] * 100 if total_by_period[period] else 0.0)
        for (brand, period), activity in activity_by_brand_period.items()
    }
