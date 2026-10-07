from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.measurement import LiftEstimate
from store.orm import LiftEstimateORM


def _to_orm(estimate: LiftEstimate) -> LiftEstimateORM:
    return LiftEstimateORM(
        id=estimate.id,
        tenant_id=estimate.tenant_id,
        created_at=estimate.created_at,
        updated_at=estimate.updated_at,
        status=estimate.status.value,
        version=estimate.version,
        brand_id=estimate.brand_id,
        test_name=estimate.test_name,
        effect=estimate.effect,
        ci_low=estimate.ci_low,
        ci_high=estimate.ci_high,
        method=estimate.method,
    )


def _to_pydantic(row: LiftEstimateORM) -> LiftEstimate:
    return LiftEstimate(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        test_name=row.test_name,
        effect=row.effect,
        ci_low=row.ci_low,
        ci_high=row.ci_high,
        method=row.method,
    )


class LiftEstimateRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, estimate: LiftEstimate) -> LiftEstimate:
        row = _to_orm(estimate)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def list_by_brand(self, brand_id: UUID) -> list[LiftEstimate]:
        rows = self.session.scalars(
            select(LiftEstimateORM).where(LiftEstimateORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
