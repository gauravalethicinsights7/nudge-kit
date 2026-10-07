from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, model_validator

from llm.client import call
from schemas.base import ProvMoney, ProvNumber
from schemas.brand import Brand
from schemas.common import EvidencedText
from schemas.evidence import Evidence
from schemas.market_landscape import PatientFunnel

PROMPTS_DIR = Path(__file__).parent / "prompts"


class QuestionCoverage(BaseModel):
    block: str
    question: str
    answered: bool
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_ids: list[UUID] = Field(default_factory=list)


class SynthesisResult(BaseModel):
    patient_funnel: PatientFunnel | None = None
    market_size: ProvMoney | None = None
    growth_pct: ProvNumber | None = None
    paradigm: EvidencedText | None = None
    access_summary: str | None = None
    unmet_needs: list[str] = Field(default_factory=list)
    key_facts: list[EvidencedText] = Field(default_factory=list)
    question_coverage: list[QuestionCoverage] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_evidence_ids_exist(self, info: ValidationInfo) -> "SynthesisResult":
        """Turns a hallucinated evidence_id into a validation error, which
        llm.client.call retries with the error appended — the concrete
        mechanism for specs/m1-research.md's 'never invent a number.'"""
        context = info.context or {}
        valid_ids = context.get("valid_evidence_ids")
        if valid_ids is None:
            return self

        cited: set[UUID] = set()
        if self.paradigm:
            cited.update(self.paradigm.evidence_ids)
        for fact in self.key_facts:
            cited.update(fact.evidence_ids)
        for coverage in self.question_coverage:
            cited.update(coverage.evidence_ids)

        invented = cited - set(valid_ids)
        if invented:
            raise ValueError(
                f"cited evidence_ids not found among persisted evidence: "
                f"{sorted(str(i) for i in invented)}"
            )
        return self


def synthesize(
    brand: Brand,
    evidence: list[Evidence],
    question_bank: dict[str, list[str]],
    *,
    run_record_repo=None,
) -> SynthesisResult:
    evidence_payload = [
        {"id": str(e.id), "type": e.type.value, "claim": e.claim, "confidence": e.confidence}
        for e in evidence
    ]
    return call(
        "synthesiser",
        {
            "brand_name": brand.name,
            "market": brand.market.value,
            "question_bank": json.dumps(question_bank),
            "evidence": json.dumps(evidence_payload),
        },
        SynthesisResult,
        model_tier="standard",
        module="m1_synthesiser",
        run_record_repo=run_record_repo,
        validation_context={"valid_evidence_ids": {e.id for e in evidence}},
        prompts_dir=PROMPTS_DIR,
    )
