"""YAML -> ContentModule[] ingest for M7 (specs/m7-orchestration.md: 'content
module library (with mlr_status)'). Nothing before this session built a
content module library at all (see the approved M7 plan's gap #1) — this is
the minimal plumbing, same spirit as ingest/channel_history_csv.py for M6.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import yaml

from schemas.content import ContentModule


def load_content_library(path: Path | str, brand_id: UUID) -> list[ContentModule]:
    data = yaml.safe_load(Path(path).read_text())
    return [ContentModule(brand_id=brand_id, **module) for module in data["modules"]]
