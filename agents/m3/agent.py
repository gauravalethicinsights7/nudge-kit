"""M3 orchestrator: routes to a derivation path, then deterministically
normalizes share_of_universe/share_of_potential across the whole run and
computes distinctness — measured and reported, not auto-corrected (the same
treatment M1 gives its rubric-style quality metrics).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from agents.m3.call_notes import CallNote
from agents.m3.call_notes import run_call_notes as _run_call_notes
from agents.m3.finalize import DerivedPersona
from agents.m3.social import SocialPost
from agents.m3.social import run_social as _run_social
from agents.m3.survey import SurveyResponse
from agents.m3.survey import run_survey as _run_survey
from agents.m3.synthetic import DEFAULT_PERSONA_COUNT
from agents.m3.synthetic import run_synthetic as _run_synthetic
from models.personas import normalize_shares, pairwise_distinctness
from schemas.brand import Brand
from schemas.market_landscape import MarketLandscape
from schemas.pack import Pack
from schemas.persona import JourneyMap, Persona
from schemas.persona_assignment import PersonaAssignment
from store.evidence_repo import EvidenceRepo
from store.journey_map_repo import JourneyMapRepo
from store.persona_assignment_repo import PersonaAssignmentRepo
from store.persona_repo import PersonaRepo


@dataclass
class M3Result:
    personas: list[Persona]
    journey_maps: list[JourneyMap]
    persona_assignments: list[PersonaAssignment]
    distinctness_violations: list[tuple[str, str, float]] = field(default_factory=list)


def _finalize_and_persist(
    derived: list[DerivedPersona], assignments: list[PersonaAssignment], session: Session
) -> M3Result:
    shares = normalize_shares([d.raw_weight for d in derived])
    for d, share in zip(derived, shares):
        d.persona.share_of_universe = share
        d.persona.share_of_potential = share

    saved_personas = PersonaRepo(session).add_many([d.persona for d in derived])
    saved_journey_maps = JourneyMapRepo(session).add_many([d.journey_map for d in derived])
    saved_assignments = (
        PersonaAssignmentRepo(session).add_many(assignments) if assignments else []
    )

    return M3Result(
        personas=saved_personas,
        journey_maps=saved_journey_maps,
        persona_assignments=saved_assignments,
        distinctness_violations=pairwise_distinctness(saved_personas),
    )


def run_synthetic(
    brand: Brand,
    pack: Pack,
    session: Session,
    market_landscape: MarketLandscape | None = None,
    persona_count: int = DEFAULT_PERSONA_COUNT,
    *,
    run_record_repo=None,
) -> M3Result:
    derived = _run_synthetic(
        brand, pack, market_landscape, persona_count, run_record_repo=run_record_repo
    )
    return _finalize_and_persist(derived, [], session)


def run_call_notes(
    brand: Brand, pack: Pack, notes: list[CallNote], session: Session, *, run_record_repo=None
) -> M3Result:
    derived, assignments = _run_call_notes(
        brand, pack, notes, EvidenceRepo(session), run_record_repo=run_record_repo
    )
    return _finalize_and_persist(derived, assignments, session)


def run_survey(
    brand: Brand,
    pack: Pack,
    responses: list[SurveyResponse],
    session: Session,
    *,
    run_record_repo=None,
) -> M3Result:
    derived = _run_survey(
        brand, pack, responses, EvidenceRepo(session), run_record_repo=run_record_repo
    )
    return _finalize_and_persist(derived, [], session)


def run_social(
    brand: Brand, pack: Pack, posts: list[SocialPost], session: Session, *, run_record_repo=None
) -> M3Result:
    derived, assignments = _run_social(
        brand, pack, posts, EvidenceRepo(session), run_record_repo=run_record_repo
    )
    return _finalize_and_persist(derived, assignments, session)
