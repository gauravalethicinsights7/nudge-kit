from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.persona_assignment import PersonaAssignment
from store.orm import PersonaAssignmentORM


def _to_orm(assignment: PersonaAssignment) -> PersonaAssignmentORM:
    return PersonaAssignmentORM(
        id=assignment.id,
        tenant_id=assignment.tenant_id,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        status=assignment.status.value,
        version=assignment.version,
        hcp_id=assignment.hcp_id,
        brand_id=assignment.brand_id,
        persona_id=assignment.persona_id,
        confidence=assignment.confidence,
    )


def _to_pydantic(row: PersonaAssignmentORM) -> PersonaAssignment:
    return PersonaAssignment(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        hcp_id=row.hcp_id,
        brand_id=row.brand_id,
        persona_id=row.persona_id,
        confidence=row.confidence,
    )


class PersonaAssignmentRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, assignments: list[PersonaAssignment]) -> list[PersonaAssignment]:
        rows = [_to_orm(a) for a in assignments]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[PersonaAssignment]:
        rows = self.session.scalars(
            select(PersonaAssignmentORM).where(PersonaAssignmentORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
