"""Data Hub: upload the files M2/M6/M7/M8 need but the engine never
persists as entities (no HCP repo; sales/content-library are transient
inputs). Each upload is parsed immediately with the real ingest loader so a
malformed file is rejected at upload time, not at module-run time."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from api.deps import get_brand_pack
from api.uploads_store import UPLOAD_KINDS, list_uploads, save_upload, upload_path
from ingest.call_notes_csv import load_call_notes_csv
from ingest.content_library import load_content_library
from ingest.engagement_events_csv import load_engagement_events_csv
from ingest.hcp_csv import load_hcp_csv
from ingest.sales_csv import load_sales_csv
from ingest.social_csv import load_social_csv
from ingest.survey_csv import load_survey_csv
from schemas.pack import Pack

router = APIRouter(prefix="/brands/{brand_id}/uploads", tags=["uploads"])


def _row_count(kind: str, brand_id: UUID, pack: Pack) -> int:
    path = upload_path(brand_id, kind)
    if kind == "hcp_sample":
        return len(load_hcp_csv(path, pack))
    if kind == "content_library":
        return len(load_content_library(path, brand_id))
    if kind == "engagement_events":
        return len(load_engagement_events_csv(path, brand_id))
    if kind == "sales":
        return len(load_sales_csv(path))
    if kind == "call_notes":
        return len(load_call_notes_csv(path))
    if kind == "survey_responses":
        return len(load_survey_csv(path))
    if kind == "social_posts":
        return len(load_social_csv(path))
    raise ValueError(f"unknown kind: {kind}")


@router.post("/{kind}")
async def upload_file(
    brand_id: UUID,
    kind: str,
    file: UploadFile,
    pack: Pack = Depends(get_brand_pack),
) -> dict:
    if kind not in UPLOAD_KINDS:
        raise HTTPException(status_code=400, detail=f"unknown upload kind: {kind}. Valid: {sorted(UPLOAD_KINDS)}")

    content = await file.read()
    save_upload(brand_id, kind, content)

    try:
        row_count = _row_count(kind, brand_id, pack)
    except Exception as e:
        # the file is already written — but an unparsable upload is still a
        # client error, not a server error, and we report it clearly rather
        # than leaving a silently-broken file in place
        raise HTTPException(status_code=400, detail=f"uploaded file failed to parse: {e}") from e

    return {"kind": kind, "filename": file.filename, "row_count": row_count}


@router.get("")
def list_brand_uploads(brand_id: UUID, pack: Pack = Depends(get_brand_pack)) -> list[dict]:
    uploads = list_uploads(brand_id)
    results = []
    for kind, path in uploads.items():
        try:
            row_count = _row_count(kind, brand_id, pack)
        except Exception:
            row_count = None
        results.append({"kind": kind, "path": str(path), "row_count": row_count})
    return results
