"""Read-only pack browser for the Admin console — packs are config
(CLAUDE.md rule 5: market specifics live in pack.yaml, never in code), never
edited through this API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth.deps import get_current_user
from packs.loader import PackLoadError, load_pack
from schemas.pack import Pack
from schemas.user import User

router = APIRouter(prefix="/packs", tags=["packs"])


@router.get("/{market}", response_model=Pack)
def get_pack(market: str, _user: User = Depends(get_current_user)) -> Pack:
    try:
        return load_pack(market)
    except PackLoadError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
