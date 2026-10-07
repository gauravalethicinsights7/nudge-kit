import json

import pytest

from agents.m1.synthesiser import synthesize
from llm.client import LLMValidationError
from tests.factories import make_brand, make_evidence

QUESTION_BANK = {"disease_patient_flow": ["What is the prevalence?"]}


def test_synthesize_accepts_valid_evidence_ids(monkeypatch):
    evidence = make_evidence()

    def fake_call(model, system, prompt):
        return (
            json.dumps(
                {
                    "key_facts": [{"text": "some fact", "evidence_ids": [str(evidence.id)]}],
                    "question_coverage": [
                        {
                            "block": "disease_patient_flow",
                            "question": "What is the prevalence?",
                            "answered": True,
                            "confidence": 0.8,
                            "evidence_ids": [str(evidence.id)],
                        }
                    ],
                }
            ),
            100,
            50,
        )

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    result = synthesize(make_brand(), [evidence], QUESTION_BANK)

    assert result.key_facts[0].evidence_ids == [evidence.id]
    assert result.question_coverage[0].confidence == 0.8


def test_synthesize_rejects_invented_evidence_id(monkeypatch):
    evidence = make_evidence()
    invented_id = "00000000-0000-0000-0000-000000000000"

    def fake_call(model, system, prompt):
        return (
            json.dumps(
                {
                    "key_facts": [{"text": "some fact", "evidence_ids": [invented_id]}],
                    "question_coverage": [],
                }
            ),
            100,
            50,
        )

    monkeypatch.setattr("llm.client._call_anthropic", fake_call)

    with pytest.raises(LLMValidationError):
        synthesize(make_brand(), [evidence], QUESTION_BANK)
