from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Rung, Status
from schemas.measurement import Outcome
from store.orm import OutcomeORM


def _to_orm(outcome: Outcome) -> OutcomeORM:
    return OutcomeORM(
        id=outcome.id,
        tenant_id=outcome.tenant_id,
        created_at=outcome.created_at,
        updated_at=outcome.updated_at,
        status=outcome.status.value,
        version=outcome.version,
        brand_id=outcome.brand_id,
        hcp_id=outcome.hcp_id,
        segment_id=outcome.segment_id,
        period=outcome.period,
        engagement_index=outcome.engagement_index,
        rung=outcome.rung.value if outcome.rung else None,
        nrx=outcome.nrx,
        trx=outcome.trx,
    )


def _to_pydantic(row: OutcomeORM) -> Outcome:
    return Outcome(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        hcp_id=row.hcp_id,
        segment_id=row.segment_id,
        period=row.period,
        engagement_index=row.engagement_index,
        rung=Rung(row.rung) if row.rung else None,
        nrx=row.nrx,
        trx=row.trx,
    )


class OutcomeRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, outcomes: list[Outcome]) -> list[Outcome]:
        rows = [_to_orm(o) for o in outcomes]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[Outcome]:
        rows = self.session.scalars(select(OutcomeORM).where(OutcomeORM.brand_id == brand_id)).all()
        return [_to_pydantic(r) for r in rows]
