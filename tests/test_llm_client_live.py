import os

import pytest
from pydantic import BaseModel

from llm.client import call

pytestmark = pytest.mark.live


class Greeting(BaseModel):
    message: str


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="requires ANTHROPIC_API_KEY")
def test_live_toy_schema_and_run_record(db_session):
    from store.run_record_repo import RunRecordRepo

    repo = RunRecordRepo(db_session)
    result = call(
        "_toy_test", {"name": "Ritesh"}, Greeting, model_tier="fast", module="foundations_toy", run_record_repo=repo
    )
    assert isinstance(result.message, str) and result.message

    records = repo.list(module="foundations_toy")
    assert len(records) >= 1
    assert records[-1].error is None
    assert records[-1].tokens_in > 0
