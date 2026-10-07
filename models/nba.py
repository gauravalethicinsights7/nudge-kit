"""Deterministic next-best-action scoring for M7 (specs/m7-orchestration.md):

    allowed_i  = channels with consent, under freq cap, compliant, content available
    score_i,a  = p_respond(i,a) * value_gain(rung_i -> rung_i+1) - cost_a
    nba_i      = top-k actions by score (k=3)

Per CLAUDE.md rule 1, every function here is a tested pure function — no LLM
calls. `allowed_i` is models/guardrails.py's job; this module is the scoring
half.

v1 p_respond, per spec: "heuristic from channel_affinity x recency decay"
(the gradient-boosted path needs >=5k labelled events, which don't exist in
this build). `days_since_last_touch=None` (no engagement-event history exists
anywhere in this build yet) decays to no penalty (1.0) rather than a
fabricated recency signal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from models.scores import p_move_up
from schemas.enums import Rung
from schemas.hcp import HCP
from schemas.pack import Pack
from schemas.persona import Persona

NEUTRAL_AFFINITY = 0.5  # a channel missing from persona.channel_affinity is treated as average
DEFAULT_HALF_LIFE_DAYS = 14.0
RUNG_STEPS = len(Rung) - 1  # 6 transitions across the 7-rung ladder


def recency_decay(days_since_last_touch: float | None, half_life_days: float = DEFAULT_HALF_LIFE_DAYS) -> float:
    """Exponential decay, 1.0 (no penalty) when there's no touch history to
    decay from — see module docstring."""
    if days_since_last_touch is None:
        return 1.0
    if days_since_last_touch < 0:
        raise ValueError(f"days_since_last_touch must be >= 0, got {days_since_last_touch}")
    return math.exp(-math.log(2) * days_since_last_touch / half_life_days)


def p_respond(persona: Persona | None, channel_ref: str, days_since_last_touch: float | None = None) -> float:
    affinity = persona.channel_affinity.get(channel_ref, NEUTRAL_AFFINITY) if persona else NEUTRAL_AFFINITY
    return affinity * recency_decay(days_since_last_touch)


def value_gain(hcp: HCP, rung: Rung, pack: Pack) -> float:
    """$-equivalent value of moving `hcp` up one rung: potential * P(move up
    this rung this month) / (rung steps in the ladder) — a per-step value
    proxy, same spirit as models.plan.revenue_at_stake's potential x
    probability derivation. Not itself a probability (that's p_respond's
    job) — this is the payoff *if* the touch lands."""
    return hcp.potential.value * p_move_up(rung, pack) / RUNG_STEPS


def score_action(p_respond_value: float, value_gain_value: float, cost: float) -> float:
    return p_respond_value * value_gain_value - cost


@dataclass
class ActionCandidate:
    channel_ref: str
    content_ref: str | None
    score: float
    p_respond_value: float
    value_gain_value: float
    cost: float


def build_action_reason(candidate: ActionCandidate) -> str:
    """Human-readable sentence from the score components, same style as
    models.scores.build_reason."""
    return (
        f"channel={candidate.channel_ref}: p(respond)={candidate.p_respond_value:.2f}, "
        f"value if moved up a rung={candidate.value_gain_value:.1f}, cost={candidate.cost:.2f} "
        f"-> score={candidate.score:.2f}."
    )


def top_k_actions(candidates: list[ActionCandidate], k: int = 3) -> list[ActionCandidate]:
    return sorted(candidates, key=lambda c: c.score, reverse=True)[:k]
