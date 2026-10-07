from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.measurement import PriorUpdate
from store.orm import PriorUpdateORM


def _to_orm(update: PriorUpdate) -> PriorUpdateORM:
    return PriorUpdateORM(
        id=update.id,
        tenant_id=update.tenant_id,
        created_at=update.created_at,
        updated_at=update.updated_at,
        status=update.status.value,
        version=update.version,
        brand_id=update.brand_id,
        prior_type=update.prior_type,
        key=update.key,
        period=update.period,
        before=update.before,
        after=update.after,
    )


def _to_pydantic(row: PriorUpdateORM) -> PriorUpdate:
    return PriorUpdate(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        prior_type=row.prior_type,
        key=row.key,
        period=row.period,
        before=row.before,
        after=row.after,
    )


class PriorUpdateRepo:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, update: PriorUpdate) -> PriorUpdate:
        """specs/m8-measurement.md Done-when: 'Prior update is idempotent and
        versioned.' Keyed on (brand_id, prior_type, key, period): re-running
        with the same inputs updates the existing row in place (bumping
        version) rather than inserting a duplicate. pack.yaml itself is never
        touched by this or any other code path — this is a separate,
        tenant-level overlay row."""
        existing = self.session.scalars(
            select(PriorUpdateORM).where(
                PriorUpdateORM.brand_id == update.brand_id,
                PriorUpdateORM.prior_type == update.prior_type,
                PriorUpdateORM.key == update.key,
                PriorUpdateORM.period == update.period,
            )
        ).first()

        if existing is None:
            row = _to_orm(update)
            self.session.add(row)
        else:
            row = existing
            row.before = update.before
            row.after = update.after
            row.version += 1
            row.updated_at = update.updated_at

        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def list_by_brand(self, brand_id: UUID) -> list[PriorUpdate]:
        rows = self.session.scalars(
            select(PriorUpdateORM).where(PriorUpdateORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
