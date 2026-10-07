"""CSV -> per-channel history ingest for M6's optional fitting input
(specs/m6-channel-mix.md: 'history CSV (period x channel spend/activity x
outcome) for fitting'). Not used by the fixture (no history exists for Brand
S) — exercised by the backtest harness and unit tests.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingest.csv_utils import read_csv_skipping_comments


def load_channel_history_csv(path: Path | str) -> dict[str, pd.DataFrame]:
    """period, channel, activity, outcome -> {channel: DataFrame(activity, outcome)},
    each sorted by period."""
    df = read_csv_skipping_comments(Path(path))
    df = df.sort_values("period")
    return {
        channel: group[["activity", "outcome"]].reset_index(drop=True)
        for channel, group in df.groupby("channel")
    }
