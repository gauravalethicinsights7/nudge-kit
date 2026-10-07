from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.content import ContentModule
from schemas.enums import Driver, MlrStatus, Status
from store.orm import ContentModuleORM


def _to_orm(content: ContentModule) -> ContentModuleORM:
    return ContentModuleORM(
        id=content.id,
        tenant_id=content.tenant_id,
        created_at=content.created_at,
        updated_at=content.updated_at,
        status=content.status.value,
        version=content.version,
        brand_id=content.brand_id,
        name=content.name,
        channel_refs=content.channel_refs,
        driver=content.driver.value,
        persona_ids=[str(p) for p in content.persona_ids],
        claim=content.claim,
        evidence_ids=[str(e) for e in content.evidence_ids],
        format=content.format,
        mlr_status=content.mlr_status.value,
        on_label=content.on_label,
        is_comparative=content.is_comparative,
        comparative_approved=content.comparative_approved,
        patient_directed=content.patient_directed,
        exceeds_pack_limit=content.exceeds_pack_limit,
    )


def _to_pydantic(row: ContentModuleORM) -> ContentModule:
    return ContentModule(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        name=row.name,
        channel_refs=row.channel_refs or [],
        driver=Driver(row.driver),
        persona_ids=[UUID(p) for p in (row.persona_ids or [])],
        claim=row.claim,
        evidence_ids=[UUID(e) for e in (row.evidence_ids or [])],
        format=row.format,
        mlr_status=MlrStatus(row.mlr_status),
        on_label=row.on_label,
        is_comparative=row.is_comparative,
        comparative_approved=row.comparative_approved,
        patient_directed=row.patient_directed,
        exceeds_pack_limit=row.exceeds_pack_limit,
    )


class ContentModuleRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, modules: list[ContentModule]) -> list[ContentModule]:
        rows = [_to_orm(m) for m in modules]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[ContentModule]:
        rows = self.session.scalars(
            select(ContentModuleORM).where(ContentModuleORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
