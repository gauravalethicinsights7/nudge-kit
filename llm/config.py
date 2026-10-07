"""Model-tier configuration.

The actual provider/tier policy and monthly cost cap are an open decision in
CLAUDE.md (owner: Ritesh). Everything here is a working default so the LLM
client is usable in dev; override any of it via env vars without code changes.
"""

import os

MODEL_TIERS: dict[str, str] = {
    "fast": os.environ.get("NUDGE_MODEL_TIER_FAST", "claude-haiku-4-5-20251001"),
    "standard": os.environ.get("NUDGE_MODEL_TIER_STANDARD", "claude-sonnet-5"),
    "deep": os.environ.get("NUDGE_MODEL_TIER_DEEP", "claude-opus-5-5"),
}

# USD per million tokens. PLACEHOLDER — confirm against Anthropic's current
# pricing page before using this for real budget/cost decisions; override via
# env if these drift.
DEFAULT_PRICING_PER_MTOK: dict[str, dict[str, float]] = {
    "fast": {
        "input": float(os.environ.get("NUDGE_PRICE_FAST_IN", "1.0")),
        "output": float(os.environ.get("NUDGE_PRICE_FAST_OUT", "5.0")),
    },
    "standard": {
        "input": float(os.environ.get("NUDGE_PRICE_STANDARD_IN", "3.0")),
        "output": float(os.environ.get("NUDGE_PRICE_STANDARD_OUT", "15.0")),
    },
    "deep": {
        "input": float(os.environ.get("NUDGE_PRICE_DEEP_IN", "15.0")),
        "output": float(os.environ.get("NUDGE_PRICE_DEEP_OUT", "75.0")),
    },
}


def resolve_model(model_tier: str) -> str:
    if model_tier not in MODEL_TIERS:
        raise ValueError(f"unknown model_tier '{model_tier}', expected one of {list(MODEL_TIERS)}")
    return MODEL_TIERS[model_tier]


def estimate_cost(model_tier: str, tokens_in: int, tokens_out: int) -> float:
    pricing = DEFAULT_PRICING_PER_MTOK[model_tier]
    return (tokens_in / 1_000_000) * pricing["input"] + (tokens_out / 1_000_000) * pricing["output"]


def get_run_budget_usd() -> float:
    return float(os.environ.get("NUDGE_RUN_BUDGET_USD", "2.00"))
