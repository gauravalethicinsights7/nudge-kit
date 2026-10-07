from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Driver, EvidenceType, PersonaDerivation, Rung, Status
from schemas.persona import Persona
from store.orm import PersonaORM


def _to_orm(persona: Persona) -> PersonaORM:
    return PersonaORM(
        id=persona.id,
        tenant_id=persona.tenant_id,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        status=persona.status.value,
        version=persona.version,
        brand_id=persona.brand_id,
        name=persona.name,
        beliefs=persona.beliefs,
        drivers_ranked=[d.value for d in persona.drivers_ranked],
        barriers_by_rung={rung.value: barriers for rung, barriers in persona.barriers_by_rung.items()},
        evidence_needs=[e.value for e in persona.evidence_needs],
        channel_affinity=persona.channel_affinity,
        influence_network=persona.influence_network,
        share_of_universe=persona.share_of_universe,
        share_of_potential=persona.share_of_potential,
        derivation=persona.derivation.value,
        evidence_ids=[str(i) for i in persona.evidence_ids],
        assumption=persona.assumption,
        confidence=persona.confidence,
    )


def _to_pydantic(row: PersonaORM) -> Persona:
    return Persona(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        name=row.name,
        beliefs=row.beliefs or [],
        drivers_ranked=[Driver(d) for d in (row.drivers_ranked or [])],
        barriers_by_rung={Rung(r): b for r, b in (row.barriers_by_rung or {}).items()},
        evidence_needs=[EvidenceType(e) for e in (row.evidence_needs or [])],
        channel_affinity=row.channel_affinity or {},
        influence_network=row.influence_network or [],
        share_of_universe=row.share_of_universe,
        share_of_potential=row.share_of_potential,
        derivation=PersonaDerivation(row.derivation),
        evidence_ids=[UUID(i) for i in (row.evidence_ids or [])],
        assumption=row.assumption,
        confidence=row.confidence,
    )


class PersonaRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, personas: list[Persona]) -> list[Persona]:
        rows = [_to_orm(p) for p in personas]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID, status: Status | None = None) -> list[Persona]:
        stmt = select(PersonaORM).where(PersonaORM.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(PersonaORM.status == status.value)
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]
