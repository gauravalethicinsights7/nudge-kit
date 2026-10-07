"""CSV -> Rx/sales-by-HCP ingest for M8 (specs/m8-measurement.md's
'Rx/sales by HCP or territory' input). No real Rx/sales feed exists anywhere
in this build — this loads a small, clearly-synthetic sample CSV.
"""

from __future__ import annotations

from pathlib import Path

from ingest.csv_utils import read_csv_skipping_comments


def load_sales_csv(path: Path | str) -> dict[tuple[str, str], tuple[float, float]]:
    """Columns: hcp_id, period (YYYY-MM), nrx, trx -> {(hcp_id, period): (nrx, trx)}."""
    df = read_csv_skipping_comments(Path(path))
    return {(str(row["hcp_id"]), str(row["period"])): (float(row["nrx"]), float(row["trx"])) for _, row in df.iterrows()}
