"""System status — lets the frontend disable LLM/web-search-gated actions
with a real reason instead of attempting and failing, same spirit as the
eval harness's own skipped_reason pattern."""

from __future__ import annotations

import os

from fastapi import APIRouter

from llm.config import get_run_budget_usd

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def get_status() -> dict:
    return {
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "serper_configured": bool(os.environ.get("SERPER_API_KEY")),
        "run_budget_usd": get_run_budget_usd(),
    }
