"""CSV -> SocialPost[] ingest for M3's social derivation path
(agents/m3/social.py). hcp_ref is optional — an unresolvable post author
simply doesn't produce a PersonaAssignment (handled downstream, not here).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from agents.m3.social import SocialPost
from ingest.csv_utils import read_csv_skipping_comments


def load_social_csv(path: Path | str) -> list[SocialPost]:
    df = read_csv_skipping_comments(Path(path))
    return [
        SocialPost(
            post_id=str(row["post_id"]),
            hcp_ref=str(row["hcp_ref"]) if not pd.isna(row.get("hcp_ref")) else None,
            text=str(row["text"]),
        )
        for _, row in df.iterrows()
    ]
