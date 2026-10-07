from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.target_list import TargetList, TargetListEntry
from store.orm import TargetListORM


def _to_orm(target_list: TargetList) -> TargetListORM:
    return TargetListORM(
        id=target_list.id,
        tenant_id=target_list.tenant_id,
        created_at=target_list.created_at,
        updated_at=target_list.updated_at,
        status=target_list.status.value,
        version=target_list.version,
        brand_id=target_list.brand_id,
        segment_id=target_list.segment_id,
        entries=[e.model_dump(mode="json") for e in target_list.entries],
    )


def _to_pydantic(row: TargetListORM) -> TargetList:
    return TargetList(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        segment_id=row.segment_id,
        entries=[TargetListEntry.model_validate(e) for e in (row.entries or [])],
    )


class TargetListRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, target_lists: list[TargetList]) -> list[TargetList]:
        rows = [_to_orm(t) for t in target_lists]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[TargetList]:
        rows = self.session.scalars(
            select(TargetListORM).where(TargetListORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
