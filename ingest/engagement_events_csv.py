"""CSV -> EngagementEvent[] ingest for M8 (specs/m8-measurement.md's
'engagement events' input). No real engagement-event history exists anywhere
in this build (M7 flagged the same gap and deferred it) — this is the
minimal plumbing, same spirit as ingest/channel_history_csv.py for M6.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from ingest.csv_utils import read_csv_skipping_comments
from schemas.engagement import EngagementEvent


def load_engagement_events_csv(path: Path | str, brand_id: UUID) -> list[EngagementEvent]:
    """Columns: hcp_id, channel, depth, occurred_at (YYYY-MM-DD), period (YYYY-MM)."""
    df = read_csv_skipping_comments(Path(path))
    return [
        EngagementEvent(
            brand_id=brand_id,
            hcp_id=UUID(row["hcp_id"]),
            channel=row["channel"],
            depth=row["depth"],
            occurred_at=row["occurred_at"],
            period=row["period"],
        )
        for _, row in df.iterrows()
    ]
