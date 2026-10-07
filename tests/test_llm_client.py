import json

import pytest
from pydantic import BaseModel

from llm.client import BudgetExceededError, LLMValidationError, call


class Greeting(BaseModel):
    message: str


class FakeRunRecordRepo:
    def __init__(self):
        self.records = []

    def add(self, record):
        self.records.append(record)
        return record


def test_succeeds_first_try(monkeypatch):
    def fake_call(model, system, prompt):
        return json.dumps({"message": "hello world"}), 5, 5

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)
    result = call("_toy_test", {"name": "World"}, Greeting)
    assert result.message == "hello world"


def test_retries_on_validation_error_then_succeeds(monkeypatch):
    attempts = []

    def fake_call(model, system, prompt):
        attempts.append(prompt)
        if len(attempts) == 1:
            return "not json at all", 10, 5
        return json.dumps({"message": "hi"}), 10, 5

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)
    repo = FakeRunRecordRepo()

    result = call("_toy_test", {"name": "World"}, Greeting, module="test", run_record_repo=repo)

    assert result.message == "hi"
    assert len(attempts) == 2
    assert "invalid" in attempts[1].lower()
    assert len(repo.records) == 1
    assert repo.records[0].error is None


def test_exhausts_retries_and_raises(monkeypatch):
    def fake_call(model, system, prompt):
        return "still not json", 10, 5

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)
    repo = FakeRunRecordRepo()

    with pytest.raises(LLMValidationError):
        call("_toy_test", {"name": "World"}, Greeting, module="test", run_record_repo=repo)

    assert len(repo.records) == 1
    assert repo.records[0].error is not None


def test_budget_exceeded_raises(monkeypatch):
    monkeypatch.setenv("NUDGE_RUN_BUDGET_USD", "0.0000001")

    def fake_call(model, system, prompt):
        return json.dumps({"message": "hi"}), 1000, 1000

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    with pytest.raises(BudgetExceededError):
        call("_toy_test", {"name": "World"}, Greeting, module="test")
