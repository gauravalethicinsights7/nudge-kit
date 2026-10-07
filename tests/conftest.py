from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import pytest  # noqa: E402

from store.db import get_session  # noqa: E402


@pytest.fixture()
def db_session():
    """Connects to the real dev Postgres (docker-compose). Tests generate
    unique data (random names/uuids) rather than relying on transactional
    rollback, so this local dev DB is safe to leave populated between runs."""
    session = get_session()
    yield session
    session.close()
