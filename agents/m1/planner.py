from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from llm.client import call
from schemas.brand import Brand
from schemas.pack import Pack

QUESTION_BANK_PATH = Path(__file__).parent / "question_bank.yaml"
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_question_bank() -> dict[str, list[str]]:
    return yaml.safe_load(QUESTION_BANK_PATH.read_text())


class PlannedQueries(BaseModel):
    queries: list[str] = Field(min_length=20, max_length=40)


def plan_queries(brand: Brand, pack: Pack, *, run_record_repo=None) -> list[str]:
    """Expands the fixed question bank into 20-40 web search queries for this
    brand + market, per specs/m1-research.md's Planner step. The 20-40 count is
    enforced by PlannedQueries itself, so llm.client.call's existing
    retry-on-validation-error loop is what makes the LLM actually hit the range."""
    question_bank = load_question_bank()
    result = call(
        "planner",
        {
            "brand_name": brand.name,
            "molecule": brand.molecule,
            "indication": brand.indication,
            "market": brand.market.value,
            "lifecycle_stage": brand.lifecycle_stage.value,
            "currency": pack.currency,
            "question_bank": json.dumps(question_bank),
        },
        PlannedQueries,
        model_tier="standard",
        module="m1_planner",
        run_record_repo=run_record_repo,
        prompts_dir=PROMPTS_DIR,
    )
    return result.queries
