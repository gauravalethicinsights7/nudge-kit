"""FastAPI dependencies: DB session re-export (see api/db_deps.py for why
it's split out), brand lookup with tenant isolation + per-user brand access,
and pack loading."""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user
from api.db_deps import get_db
from packs.loader import PackLoadError, load_pack
from schemas.brand import Brand
from schemas.enums import UserRole
from schemas.pack import Pack
from schemas.user import User
from store.brand_repo import BrandRepo
from store.user_repo import UserBrandAccessRepo

__all__ = ["get_db", "get_brand", "get_brand_pack", "require_anthropic", "require_serper"]


def get_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Brand:
    """404s (not 403) across tenants — a brand in another tenant should look
    exactly like a brand that doesn't exist. Within the user's own tenant,
    platform_admin and brand_manager (who can create brands) see everything;
    every other role needs an explicit UserBrandAccess grant (the blueprint's
    'a user sees only brands they are assigned to')."""
    brand = BrandRepo(db).get(brand_id)
    if brand is None or brand.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail=f"brand {brand_id} not found")

    if user.role not in (UserRole.platform_admin, UserRole.brand_manager):
        if not UserBrandAccessRepo(db).has_access(user.id, brand_id):
            raise HTTPException(status_code=404, detail=f"brand {brand_id} not found")

    return brand


def get_brand_pack(brand: Brand = Depends(get_brand)) -> Pack:
    try:
        return load_pack(brand.market)
    except PackLoadError as e:
        raise HTTPException(status_code=500, detail=f"pack load failed for market={brand.market}: {e}") from e


def require_anthropic() -> None:
    """Same gate the eval harness uses (returns skipped_reason instead of
    attempting and failing) — here surfaced as 409 so the frontend can show
    a clear reason rather than a stack trace."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=409, detail="ANTHROPIC_API_KEY is not configured")


def require_serper() -> None:
    if not os.environ.get("SERPER_API_KEY"):
        raise HTTPException(status_code=409, detail="SERPER_API_KEY is not configured — web research is unavailable")
