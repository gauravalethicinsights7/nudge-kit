"""Per-brand uploaded-file storage for data the engine never persists as its
own entity (HCPs have no repo; sales/content-library/engagement-events are
transient inputs to M2/M6/M7/M8). Mirrors exactly how the eval harness reads
fixture files from disk — this just makes "disk" per-brand and uploadable.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

UPLOADS_ROOT = Path(__file__).parent.parent / "var" / "uploads"

UPLOAD_KINDS = {
    "hcp_sample": ".csv",
    "content_library": ".yaml",
    "engagement_events": ".csv",
    "sales": ".csv",
    "call_notes": ".csv",
    "survey_responses": ".csv",
    "social_posts": ".csv",
}


def _brand_dir(brand_id: UUID) -> Path:
    path = UPLOADS_ROOT / str(brand_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def upload_path(brand_id: UUID, kind: str) -> Path:
    if kind not in UPLOAD_KINDS:
        raise ValueError(f"unknown upload kind: {kind}")
    return _brand_dir(brand_id) / f"{kind}{UPLOAD_KINDS[kind]}"


def save_upload(brand_id: UUID, kind: str, content: bytes) -> Path:
    path = upload_path(brand_id, kind)
    path.write_bytes(content)
    return path


def get_existing_upload(brand_id: UUID, kind: str) -> Path | None:
    path = upload_path(brand_id, kind)
    return path if path.exists() else None


def list_uploads(brand_id: UUID) -> dict[str, Path]:
    return {kind: path for kind in UPLOAD_KINDS if (path := get_existing_upload(brand_id, kind)) is not None}
