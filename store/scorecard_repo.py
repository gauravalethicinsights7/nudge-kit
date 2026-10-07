from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.measurement import KpiResult, Scorecard
from store.orm import ScorecardORM


def _to_orm(scorecard: Scorecard) -> ScorecardORM:
    return ScorecardORM(
        id=scorecard.id,
        tenant_id=scorecard.tenant_id,
        created_at=scorecard.created_at,
        updated_at=scorecard.updated_at,
        status=scorecard.status.value,
        version=scorecard.version,
        brand_id=scorecard.brand_id,
        period=scorecard.period,
        kpis=[k.model_dump(mode="json") for k in scorecard.kpis],
    )


def _to_pydantic(row: ScorecardORM) -> Scorecard:
    return Scorecard(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        period=row.period,
        kpis=[KpiResult.model_validate(k) for k in (row.kpis or [])],
    )


class ScorecardRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, scorecard: Scorecard) -> Scorecard:
        row = _to_orm(scorecard)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get_latest_for_brand(self, brand_id: UUID) -> Scorecard | None:
        row = self.session.scalars(
            select(ScorecardORM).where(ScorecardORM.brand_id == brand_id).order_by(ScorecardORM.created_at.desc())
        ).first()
        return _to_pydantic(row) if row else None
