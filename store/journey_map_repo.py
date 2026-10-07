from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.persona import JourneyMap, JourneyStep
from store.orm import JourneyMapORM


def _to_orm(journey_map: JourneyMap) -> JourneyMapORM:
    return JourneyMapORM(
        id=journey_map.id,
        tenant_id=journey_map.tenant_id,
        created_at=journey_map.created_at,
        updated_at=journey_map.updated_at,
        status=journey_map.status.value,
        version=journey_map.version,
        brand_id=journey_map.brand_id,
        persona_id=journey_map.persona_id,
        steps=[s.model_dump(mode="json") for s in journey_map.steps],
    )


def _to_pydantic(row: JourneyMapORM) -> JourneyMap:
    return JourneyMap(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        persona_id=row.persona_id,
        steps=[JourneyStep.model_validate(s) for s in (row.steps or [])],
    )


class JourneyMapRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, journey_maps: list[JourneyMap]) -> list[JourneyMap]:
        rows = [_to_orm(j) for j in journey_maps]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID, status: Status | None = None) -> list[JourneyMap]:
        stmt = select(JourneyMapORM).where(JourneyMapORM.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(JourneyMapORM.status == status.value)
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]
