from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.early_warning_signal import EarlyWarningSignal
from schemas.enums import Status
from store.orm import EarlyWarningSignalORM


def _to_orm(signal: EarlyWarningSignal) -> EarlyWarningSignalORM:
    return EarlyWarningSignalORM(
        id=signal.id,
        tenant_id=signal.tenant_id,
        created_at=signal.created_at,
        updated_at=signal.updated_at,
        status=signal.status.value,
        version=signal.version,
        brand_id=signal.brand_id,
        type=signal.type,
        detection_rule=signal.detection_rule,
        affected_segments=signal.affected_segments,
        evidence_ids=[str(i) for i in signal.evidence_ids],
    )


def _to_pydantic(row: EarlyWarningSignalORM) -> EarlyWarningSignal:
    return EarlyWarningSignal(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        type=row.type,
        detection_rule=row.detection_rule,
        affected_segments=row.affected_segments or [],
        evidence_ids=[UUID(i) for i in (row.evidence_ids or [])],
    )


class EarlyWarningSignalRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, signals: list[EarlyWarningSignal]) -> list[EarlyWarningSignal]:
        rows = [_to_orm(s) for s in signals]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[EarlyWarningSignal]:
        rows = self.session.scalars(
            select(EarlyWarningSignalORM).where(EarlyWarningSignalORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]
