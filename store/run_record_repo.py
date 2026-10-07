from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.run_record import RunRecord
from store.orm import RunRecordORM


def _to_orm(record: RunRecord) -> RunRecordORM:
    return RunRecordORM(
        id=record.id,
        tenant_id=record.tenant_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        status=record.status.value,
        version=record.version,
        module=record.module,
        inputs_hash=record.inputs_hash,
        prompt_versions=record.prompt_versions,
        model=record.model,
        tokens_in=record.tokens_in,
        tokens_out=record.tokens_out,
        cost=record.cost,
        duration_ms=record.duration_ms,
        output_ids=[str(i) for i in record.output_ids],
        error=record.error,
    )


def _to_pydantic(row: RunRecordORM) -> RunRecord:
    return RunRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        module=row.module,
        inputs_hash=row.inputs_hash,
        prompt_versions=row.prompt_versions or {},
        model=row.model,
        tokens_in=row.tokens_in,
        tokens_out=row.tokens_out,
        cost=row.cost,
        duration_ms=row.duration_ms,
        output_ids=row.output_ids or [],
        error=row.error,
    )


class RunRecordRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, record: RunRecord) -> RunRecord:
        row = _to_orm(record)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def list(self, module: str | None = None) -> list[RunRecord]:
        stmt = select(RunRecordORM)
        if module:
            stmt = stmt.where(RunRecordORM.module == module)
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]
