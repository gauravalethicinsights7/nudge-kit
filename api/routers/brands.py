from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user
from api.db_deps import get_db
from api.deps import get_brand
from schemas.brand import Brand
from schemas.enums import LifecycleStage, Market, UserRole
from schemas.user import User
from store.brand_repo import BrandRepo
from store.user_repo import UserBrandAccessRepo

router = APIRouter(prefix="/brands", tags=["brands"])


class CreateBrandRequest(BaseModel):
    name: str
    molecule: str
    indication: str
    market: Market
    lifecycle_stage: LifecycleStage
    company: str
    price_band: str | None = None
    notes: str | None = None


@router.post("", response_model=Brand)
def create_brand(body: CreateBrandRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Brand:
    brand = Brand(
        tenant_id=user.tenant_id,
        name=body.name,
        molecule=body.molecule,
        indication=body.indication,
        market=body.market,
        lifecycle_stage=body.lifecycle_stage,
        company=body.company,
        price_band=body.price_band,
        notes=body.notes,
    )
    return BrandRepo(db).add(brand)


@router.get("", response_model=list[Brand])
def list_brands(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Brand]:
    tenant_brands = BrandRepo(db).list_by_tenant(user.tenant_id)
    if user.role in (UserRole.platform_admin, UserRole.brand_manager):
        return tenant_brands
    accessible_ids = set(UserBrandAccessRepo(db).list_brand_ids_for_user(user.id))
    return [b for b in tenant_brands if b.id in accessible_ids]


@router.get("/{brand_id}", response_model=Brand)
def get_brand_route(brand_id: UUID, brand: Brand = Depends(get_brand)) -> Brand:
    return brand
