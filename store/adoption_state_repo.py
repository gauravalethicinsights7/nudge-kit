from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Rung, Status
from schemas.hcp import AdoptionState
from store.orm import AdoptionStateORM


def _to_orm(state: AdoptionState) -> AdoptionStateORM:
    return AdoptionStateORM(
        id=state.id,
        tenant_id=state.tenant_id,
        created_at=state.created_at,
        updated_at=state.updated_at,
        status=state.status.value,
        version=state.version,
        hcp_id=state.hcp_id,
        brand_id=state.brand_id,
        rung=state.rung.value,
        entered_on=state.entered_on,
        p_move_up=state.p_move_up,
        measured=state.measured,
        rung_confidence=state.rung_confidence,
    )


def _to_pydantic(row: AdoptionStateORM) -> AdoptionState:
    return AdoptionState(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        hcp_id=row.hcp_id,
        brand_id=row.brand_id,
        rung=Rung(row.rung),
        entered_on=row.entered_on,
        p_move_up=row.p_move_up,
        measured=row.measured,
        rung_confidence=row.rung_confidence,
    )


class AdoptionStateRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, states: list[AdoptionState]) -> list[AdoptionState]:
        rows = [_to_orm(s) for s in states]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[AdoptionState]:
        rows = self.session.scalars(
            select(AdoptionStateORM).where(AdoptionStateORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
