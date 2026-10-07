"""Run-record history (cost/token transparency) for the Admin console —
CLAUDE.md: 'Every run writes a RunRecord ... log prompt version, model,
tokens, cost, duration.'"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.auth.deps import require_role
from api.deps import get_db
from schemas.enums import UserRole
from schemas.run_record import RunRecord
from schemas.user import User
from store.run_record_repo import RunRecordRepo

router = APIRouter(prefix="/run-records", tags=["run-records"])


@router.get("", response_model=list[RunRecord])
def list_run_records(
    module: str | None = None, db: Session = Depends(get_db), _user: User = Depends(require_role(UserRole.platform_admin))
) -> list[RunRecord]:
    # NB: RunRecordORM carries no brand_id/tenant_id column (a pre-existing
    # gap from the F session, not introduced here) — this lists ALL tenants'
    # run records, so it's restricted to platform_admin rather than any
    # authenticated user, to limit cross-tenant exposure.
    return RunRecordRepo(db).list(module)
