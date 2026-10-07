"""Per-brand uploaded-file storage for data the engine never persists as its
own entity (HCPs have no repo; sales/content-library/engagement-events are
transient inputs to M2/M6/M7/M8).

The bytes live in Postgres, not on disk: the API runs on hosts with an
ephemeral filesystem, where a restart would otherwise drop every upload and
break those modules until someone noticed. Callers still get a `Path` —
the ingest loaders and the eval harness both read fixtures from disk, and
keeping that contract means none of them had to change. The local file is a
cache, rebuilt from the database whenever it's missing.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from schemas.base import utcnow
from store.db import get_session
from store.orm import UploadORM

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


def _cache_path(brand_id: UUID, kind: str) -> Path:
    if kind not in UPLOAD_KINDS:
        raise ValueError(f"unknown upload kind: {kind}")
    return _brand_dir(brand_id) / f"{kind}{UPLOAD_KINDS[kind]}"


def _load_bytes(brand_id: UUID, kind: str) -> bytes | None:
    session = get_session()
    try:
        row = session.scalar(
            select(UploadORM).where(UploadORM.brand_id == brand_id, UploadORM.kind == kind)
        )
        return row.content if row else None
    finally:
        session.close()


def upload_path(brand_id: UUID, kind: str) -> Path:
    """Path to the file, materializing it from the database if the local
    cache is cold (fresh container, or evicted disk)."""
    path = _cache_path(brand_id, kind)
    if not path.exists():
        content = _load_bytes(brand_id, kind)
        if content is not None:
            path.write_bytes(content)
    return path


def save_upload(brand_id: UUID, kind: str, content: bytes) -> Path:
    if kind not in UPLOAD_KINDS:
        raise ValueError(f"unknown upload kind: {kind}")

    session = get_session()
    try:
        row = session.scalar(
            select(UploadORM).where(UploadORM.brand_id == brand_id, UploadORM.kind == kind)
        )
        if row is None:
            session.add(UploadORM(brand_id=brand_id, kind=kind, content=content))
        else:
            row.content = content
            row.updated_at = utcnow()
        session.commit()
    finally:
        session.close()

    path = _cache_path(brand_id, kind)
    path.write_bytes(content)
    return path


def get_existing_upload(brand_id: UUID, kind: str) -> Path | None:
    if _load_bytes(brand_id, kind) is None:
        return None
    return upload_path(brand_id, kind)


def list_uploads(brand_id: UUID) -> dict[str, Path]:
    session = get_session()
    try:
        kinds = session.scalars(
            select(UploadORM.kind).where(UploadORM.brand_id == brand_id)
        ).all()
    finally:
        session.close()
    return {kind: upload_path(brand_id, kind) for kind in kinds if kind in UPLOAD_KINDS}
