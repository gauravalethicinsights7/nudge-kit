"""The approval mechanism behind CLAUDE.md rule 8: 'only an approval call
sets status=approved, and downstream modules read approved objects only.'
`approve_all_for_brand` is the original bulk mechanism (still what the eval
harness uses); `approve_one`/`reject_one` are the per-object counterparts the
Approvals Inbox's individual-row decide buttons call (api/routers/approvals.py).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from schemas.enums import Status


def approve_all_for_brand(session: Session, orm_class, brand_id: UUID) -> int:
    """Sets status='approved' on every row of `orm_class` for this brand.
    Returns the number of rows updated."""
    result = session.execute(
        update(orm_class).where(orm_class.brand_id == brand_id).values(status=Status.approved.value)
    )
    session.commit()
    return result.rowcount


def approve_one(session: Session, orm_class, object_id: UUID) -> bool:
    """Sets status='approved' on exactly one row. Returns whether a row was found."""
    result = session.execute(update(orm_class).where(orm_class.id == object_id).values(status=Status.approved.value))
    session.commit()
    return result.rowcount > 0


def reject_one(session: Session, orm_class, object_id: UUID) -> bool:
    """A rejection leaves status as-is (still 'draft', not a new status value
    — see schemas/review.py's module docstring); the decision itself is
    recorded as a ReviewDecision row by the caller. This just confirms the
    object exists, for the API to 404 on a bad id rather than silently no-op."""
    row = session.get(orm_class, object_id)
    return row is not None
