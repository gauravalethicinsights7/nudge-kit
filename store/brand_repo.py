from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.brand import Brand
from schemas.enums import LifecycleStage, Market, Status
from store.orm import BrandORM


def _to_orm(brand: Brand) -> BrandORM:
    return BrandORM(
        id=brand.id,
        tenant_id=brand.tenant_id,
        created_at=brand.created_at,
        updated_at=brand.updated_at,
        status=brand.status.value,
        version=brand.version,
        name=brand.name,
        molecule=brand.molecule,
        indication=brand.indication,
        market=brand.market.value,
        lifecycle_stage=brand.lifecycle_stage.value,
        company=brand.company,
        price_band=brand.price_band,
        notes=brand.notes,
    )


def _to_pydantic(row: BrandORM) -> Brand:
    return Brand(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        name=row.name,
        molecule=row.molecule,
        indication=row.indication,
        market=Market(row.market),
        lifecycle_stage=LifecycleStage(row.lifecycle_stage),
        company=row.company,
        price_band=row.price_band,
        notes=row.notes,
    )


class BrandRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, brand: Brand) -> Brand:
        row = _to_orm(brand)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get(self, brand_id: UUID) -> Brand | None:
        row = self.session.get(BrandORM, brand_id)
        return _to_pydantic(row) if row else None

    def list_all(self) -> list[Brand]:
        rows = self.session.scalars(select(BrandORM).order_by(BrandORM.created_at.desc())).all()
        return [_to_pydantic(r) for r in rows]

    def list_by_tenant(self, tenant_id: UUID) -> list[Brand]:
        rows = self.session.scalars(
            select(BrandORM).where(BrandORM.tenant_id == tenant_id).order_by(BrandORM.created_at.desc())
        ).all()
        return [_to_pydantic(r) for r in rows]
