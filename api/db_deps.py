"""Split out from api/deps.py to break a circular import: api/deps.py's
get_brand needs the current user (api/auth/deps.py) for tenant isolation,
and api/auth/deps.py needs a DB session — both can depend on this tiny
module without depending on each other.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from store.db import get_session


def get_db() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()
