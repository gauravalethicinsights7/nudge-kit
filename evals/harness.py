from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, Field


@dataclass
class DeterministicCheck:
    name: str
    fn: Callable[[], tuple[bool, str]]


@dataclass
class RubricCriterion:
    id: str
    desc: str


class RubricScore(BaseModel):
    criterion: str
    score: int = Field(ge=1, le=5)
    rationale: str


class RubricJudgement(BaseModel):
    scores: list[RubricScore]


def run_deterministic_checks(checks: list[DeterministicCheck]) -> list[dict]:
    results = []
    for check in checks:
        try:
            passed, detail = check.fn()
        except Exception as e:  # a check that raises is a failed check, not a crash
            passed, detail = False, f"error: {e}"
        results.append({"name": check.name, "pass": bool(passed), "detail": detail})
    return results


def run_rubric(
    output_text: str,
    criteria: list[RubricCriterion],
    *,
    judge_model_tier: str = "deep",
    generator_model_tier: str = "standard",
    module: str = "eval",
    run_record_repo=None,
) -> list[dict]:
    """LLM-judge rubric scoring. Per evals/rubrics.yaml, the judge must use a
    different model tier from whatever generated output_text."""
    if judge_model_tier == generator_model_tier:
        raise ValueError("rubric judge must use a different model tier from the generator")

    from llm.client import call  # local import: avoids a hard Anthropic-SDK dependency
    # for callers (like the dummy module) that only run deterministic checks.

    prompt_vars = {
        "output_text": output_text,
        "criteria": json.dumps([{"id": c.id, "desc": c.desc} for c in criteria]),
    }
    judgement = call(
        "rubric_judge",
        prompt_vars,
        RubricJudgement,
        model_tier=judge_model_tier,
        module=module,
        run_record_repo=run_record_repo,
    )
    return [s.model_dump() for s in judgement.scores]


def build_report(checks: list[dict], rubric: list[dict]) -> dict:
    checks_pass = all(c["pass"] for c in checks)
    mean_score = None
    min_score = None
    rubric_pass = True
    if rubric:
        mean_score = sum(r["score"] for r in rubric) / len(rubric)
        min_score = min(r["score"] for r in rubric)
        # Pass bar per evals/rubrics.yaml: mean >= 4.0 and no criterion < 3
        rubric_pass = mean_score >= 4.0 and min_score >= 3

    return {
        "checks": checks,
        "rubric": rubric,
        "overall": {
            "pass": checks_pass and rubric_pass,
            "mean_rubric_score": mean_score,
            "min_rubric_score": min_score,
        },
    }
