"""Shared CSV-reading helper for /ingest adapters."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd


def read_csv_skipping_comments(path: Path) -> pd.DataFrame:
    """Fixture CSVs (scripts/generate_*_fixture.py) document themselves with
    leading '#'-prefixed comment lines; this skips them before parsing."""
    lines = [line for line in path.read_text().splitlines() if not line.startswith("#")]
    return pd.read_csv(StringIO("\n".join(lines)))
