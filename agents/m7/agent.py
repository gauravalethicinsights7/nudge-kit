"""M7 orchestrator (specs/m7-orchestration.md): build JourneyRule[] for every
T1/T3 segment x persona, then a weekly per-HCP Action[] feed, guardrail-
checked before anything is persisted or exported. Like M2/M6, this is fully
deterministic — no LLM calls anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from agents.m6.channels import build_channels_from_pack
from models.guardrails import check_action_guardrails, content_is_usable
from models.nba import (
    ActionCandidate,
    build_action_reason,
    p_respond,
    score_action,
    top_k_actions,
    value_gain,
)
from schemas.brand import Brand
from schemas.channel import Channel
from schemas.content import ContentBrief, ContentModule
from schemas.enums import Tier
from schemas.hcp import HCP, AdoptionState, Segment
from schemas.orchestration import Action, Escalation, JourneyRule, JourneyStepRule
from schemas.pack import Pack
from schemas.persona import JourneyMap, Persona
from schemas.persona_assignment import PersonaAssignment
from store.action_repo import ActionRepo
from store.content_repo import ContentModuleRepo
from store.journey_rule_repo import JourneyRuleRepo

# specs/m7-orchestration.md fixture requirement: "journey rules for every
# persona x T1/T3 segment."
JOURNEY_RULE_TIERS = {Tier.t1_grow, Tier.t3_develop}
DIGITAL_REINFORCEMENT_WAIT_DAYS = 2  # spec: "Digital reinforcement 2-3 days after a rep visit"
TOP_K_ACTIONS = 3  # spec: "nba_i = top-k actions by score (k=3)"
DEFAULT_EXIT_SIGNAL = "first_rx"


@dataclass
class M7Result:
    channels: list[Channel]
    content_modules: list[ContentModule]
    journey_rules: list[JourneyRule]
    actions: list[Action]
    content_briefs: list[ContentBrief]


def _representative_persona(personas: list[Persona]) -> Persona | None:
    return max(personas, key=lambda p: p.share_of_potential, default=None)


def _top_channel(persona: Persona, channels: list[Channel]) -> str:
    if persona.channel_affinity:
        return max(persona.channel_affinity, key=persona.channel_affinity.get)
    return channels[0].channel_ref


def _resolve_content(channel_ref: str, persona: Persona, content_library: list[ContentModule]) -> ContentModule | None:
    """Channel usable, content-level clean (mlr approved, on-label, comparative
    signed off, not patient-directed, not over a pack limit), and targeted at
    this persona (or generic). Prefers the persona's top-ranked driver, but
    falls back to any usable match rather than over-narrowing."""
    candidates = [
        c
        for c in content_library
        if channel_ref in c.channel_refs and content_is_usable(c) and (not c.persona_ids or persona.id in c.persona_ids)
    ]
    if not candidates:
        return None
    top_driver = persona.drivers_ranked[0] if persona.drivers_ranked else None
    preferred = [c for c in candidates if c.driver == top_driver]
    return (preferred or candidates)[0]


def _content_brief_for_gap(brand: Brand, persona: Persona, channel_ref: str, content_library: list[ContentModule]) -> ContentBrief:
    driver = persona.drivers_ranked[0] if persona.drivers_ranked else next(iter(persona.channel_affinity), None)
    same_channel_formats = {c.format for c in content_library if channel_ref in c.channel_refs}
    fmt = next(iter(same_channel_formats), "unspecified")
    return ContentBrief(
        brand_id=brand.id,
        driver=driver,
        persona_id=persona.id,
        channel=channel_ref,
        format=fmt,
        claim_needed=f"On-label, MLR-approved {driver.value if driver else 'generic'} claim for {persona.name} on {channel_ref}",
        reason="no usable (mlr-approved, on-label, non-patient-directed) content module found for this persona/channel",
    )


def _default_exit_signal(pack: Pack) -> str:
    return DEFAULT_EXIT_SIGNAL if DEFAULT_EXIT_SIGNAL in pack.signals else pack.signals[-1]


def _build_journey_rule(
    brand: Brand,
    segment: Segment,
    persona: Persona,
    channels: list[Channel],
    content_library: list[ContentModule],
    pack: Pack,
    journey_maps: list[JourneyMap] | None,
) -> tuple[JourneyRule, list[ContentBrief]]:
    briefs: list[ContentBrief] = []
    top_channel_ref = _top_channel(persona, channels)

    content = _resolve_content(top_channel_ref, persona, content_library)
    steps = [JourneyStepRule(channel=top_channel_ref, content_ref=str(content.id) if content else None, wait_days=0)]
    if content is None:
        briefs.append(_content_brief_for_gap(brand, persona, top_channel_ref, content_library))

    if top_channel_ref == "rep_visit":
        digital_channel_ref = next(
            (c.channel_ref for c in channels if c.channel_ref != "rep_visit" and persona.channel_affinity.get(c.channel_ref, 0.0) > 0),
            None,
        )
        if digital_channel_ref:
            digital_content = _resolve_content(digital_channel_ref, persona, content_library)
            steps.append(
                JourneyStepRule(
                    channel=digital_channel_ref,
                    content_ref=str(digital_content.id) if digital_content else None,
                    wait_days=DIGITAL_REINFORCEMENT_WAIT_DAYS,
                )
            )
            if digital_content is None:
                briefs.append(_content_brief_for_gap(brand, persona, digital_channel_ref, content_library))

    exit_signal = _default_exit_signal(pack)
    matching_journey_map = next((jm for jm in (journey_maps or []) if jm.persona_id == persona.id), None)
    if matching_journey_map and matching_journey_map.steps:
        exit_signal = matching_journey_map.steps[-1].exit_signal

    rule = JourneyRule(
        brand_id=brand.id,
        segment_id=segment.id,
        persona_id=persona.id,
        entry_criteria={"tier": segment.tier.value, "persona_id": str(persona.id)},
        steps=steps,
        escalation=[Escalation(signal="detail_requested", action="escalate_to_rep")],
        exit_signal=exit_signal,
    )
    return rule, briefs


def run(
    brand: Brand,
    pack: Pack,
    session: Session,
    segments: list[Segment],
    personas: list[Persona],
    hcps: list[HCP],
    adoption_states: list[AdoptionState],
    content_library: list[ContentModule],
    journey_maps: list[JourneyMap] | None = None,
    persona_assignments: list[PersonaAssignment] | None = None,
    recent_touches: dict[tuple[UUID, str], int] | None = None,
    unanswered_touches: dict[tuple[UUID, str], int] | None = None,
    rep_count: int | None = None,
    as_of: date | None = None,
) -> M7Result:
    as_of = as_of or date.today()
    recent_touches = recent_touches or {}
    unanswered_touches = unanswered_touches or {}

    channels = build_channels_from_pack(pack, rep_count=rep_count, as_of=as_of)
    saved_content = ContentModuleRepo(session).add_many(content_library)

    representative_persona = _representative_persona(personas)
    persona_id_by_hcp = {a.hcp_id: a.persona_id for a in (persona_assignments or [])}
    persona_by_id = {p.id: p for p in personas}

    journey_rules: list[JourneyRule] = []
    content_briefs: list[ContentBrief] = []
    for segment in segments:
        if segment.tier not in JOURNEY_RULE_TIERS:
            continue
        for persona in personas:
            rule, briefs = _build_journey_rule(brand, segment, persona, channels, saved_content, pack, journey_maps)
            journey_rules.append(rule)
            content_briefs.extend(briefs)
    saved_journey_rules = JourneyRuleRepo(session).add_many(journey_rules)

    adoption_by_hcp = {a.hcp_id: a for a in adoption_states}
    actions: list[Action] = []
    for hcp in hcps:
        adoption_state = adoption_by_hcp.get(hcp.id)
        if adoption_state is None:
            continue
        persona = persona_by_id.get(persona_id_by_hcp.get(hcp.id)) or representative_persona
        if persona is None:
            continue

        candidates: list[ActionCandidate] = []
        for channel in channels:
            content = _resolve_content(channel.channel_ref, persona, saved_content)
            if content is None:
                continue  # spec: "content available" is part of allowed_i
            recent_touch_count = recent_touches.get((hcp.id, channel.channel_ref), 0)
            unanswered_touch_count = unanswered_touches.get((hcp.id, channel.channel_ref), 0)
            violations = check_action_guardrails(
                hcp, channel.channel_ref, content, pack, recent_touch_count, unanswered_touch_count
            )
            if violations:
                continue

            p_r = p_respond(persona, channel.channel_ref, days_since_last_touch=None)
            v_g = value_gain(hcp, adoption_state.rung, pack)
            cost = channel.unit_cost.value if channel.unit_cost else 1.0
            candidates.append(
                ActionCandidate(
                    channel_ref=channel.channel_ref,
                    content_ref=str(content.id),
                    score=score_action(p_r, v_g, cost),
                    p_respond_value=p_r,
                    value_gain_value=v_g,
                    cost=cost,
                )
            )

        for candidate in top_k_actions(candidates, k=TOP_K_ACTIONS):
            actions.append(
                Action(
                    brand_id=brand.id,
                    hcp_id=hcp.id,
                    channel=candidate.channel_ref,
                    content_ref=candidate.content_ref,
                    suggested_date=as_of,
                    reason=build_action_reason(candidate),
                    score=candidate.score,
                )
            )
    saved_actions = ActionRepo(session).add_many(actions)

    return M7Result(
        channels=channels,
        content_modules=saved_content,
        journey_rules=saved_journey_rules,
        actions=saved_actions,
        content_briefs=content_briefs,
    )
