"""CSV -> CallNote[] ingest, per CLAUDE.md's /ingest layout."""

from __future__ import annotations

from pathlib import Path

from agents.m3.call_notes import CallNote
from ingest.csv_utils import read_csv_skipping_comments


def load_call_notes_csv(path: Path | str) -> list[CallNote]:
    df = read_csv_skipping_comments(Path(path))
    return [
        CallNote(note_id=str(row["note_id"]), crm_id=str(row["crm_id"]), text=row["text"])
        for _, row in df.iterrows()
    ]
