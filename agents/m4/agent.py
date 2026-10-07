"""M4 orchestrator: competitor set -> harvest claims/events (incl. our brand)
-> grid -> whitespace/parity -> ESOV (if data given) -> EarlyWarningSignal[].
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, model_validator
from sqlalchemy.orm import Session

from agents.m4.competitor_set import propose_competitor_set
from agents.m4.harvester import harvest_claims_and_events
from llm.client import call
from models.competition import (
    build_grid,
    compute_driver_importance,
    compute_esov,
    find_parity_risks,
    find_whitespace,
)
from schemas.brand import Brand
from schemas.competitive import Competitor, MessageMap
from schemas.early_warning_signal import EarlyWarningSignal, EarlyWarningType
from schemas.evidence import Evidence
from schemas.market_landscape import MarketLandscape
from schemas.pack import Pack
from schemas.persona import Persona
from store.competitor_repo import CompetitorRepo
from store.early_warning_signal_repo import EarlyWarningSignalRepo
from store.evidence_repo import EvidenceRepo
from store.message_map_repo import MessageMapRepo

PROMPTS_DIR = Path(__file__).parent / "prompts"
RECENT_EVENT_WINDOW_DAYS = 365  # spec: "in the last 12 months"


class EarlyWarningSignalDraft(BaseModel):
    type: EarlyWarningType
    detection_rule: str
    affected_segments: list[str] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)


class EarlyWarningSignalDraftList(BaseModel):
    signals: list[EarlyWarningSignalDraft] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_evidence_ids(self, info: ValidationInfo) -> "EarlyWarningSignalDraftList":
        context = info.context or {}
        valid_ids = context.get("valid_evidence_ids")
        if valid_ids is None:
            return self
        cited = {i for d in self.signals for i in d.evidence_ids}
        invented = cited - set(valid_ids)
        if invented:
            raise ValueError(
                f"cited evidence_ids not found among harvested events: {sorted(str(i) for i in invented)}"
            )
        return self


@dataclass
class M4Result:
    competitors: list[Competitor]
    message_map: MessageMap
    early_warning_signals: list[EarlyWarningSignal]
    esov_skipped_reason: str | None


def _define_early_warning_signals(
    brand: Brand, recent_events: list[tuple[str, object]], *, run_record_repo=None
) -> list[EarlyWarningSignal]:
    if not recent_events:
        return []

    events_summary = "\n".join(
        f"[{competitor_brand}] {event.date} ({event.type}): {event.text} (evidence_id={event.evidence_id})"
        for competitor_brand, event in recent_events
    )

    result = call(
        "define_early_warning_signals",
        {"brand_name": brand.name, "events_summary": events_summary},
        EarlyWarningSignalDraftList,
        model_tier="standard",
        module="m4_early_warning",
        run_record_repo=run_record_repo,
        validation_context={"valid_evidence_ids": {event.evidence_id for _, event in recent_events}},
        prompts_dir=PROMPTS_DIR,
    )
    return [
        EarlyWarningSignal(
            brand_id=brand.id,
            type=draft.type,
            detection_rule=draft.detection_rule,
            affected_segments=draft.affected_segments,
            evidence_ids=draft.evidence_ids,
        )
        for draft in result.signals
    ]


def run(
    brand: Brand,
    pack: Pack,
    session: Session,
    market_landscape: MarketLandscape | None = None,
    personas: list[Persona] | None = None,
    evidence: list[Evidence] | None = None,
    sov_by_brand_period: dict[tuple[str, str], float] | None = None,
    som_by_brand_period: dict[tuple[str, str], float] | None = None,
    *,
    run_record_repo=None,
) -> M4Result:
    evidence = evidence or []
    personas = personas or []
    evidence_repo = EvidenceRepo(session)

    proposed = propose_competitor_set(brand, market_landscape, evidence, run_record_repo=run_record_repo)

    brand_claims: dict[str, list] = {}
    events_by_brand: dict[str, list] = {}

    our_claims, our_events = harvest_claims_and_events(
        brand.name, brand.id, evidence_repo, run_record_repo=run_record_repo
    )
    brand_claims[brand.name] = our_claims
    events_by_brand[brand.name] = our_events

    company_by_brand: dict[str, str] = {}
    for proposed_competitor in proposed:
        claims, events = harvest_claims_and_events(
            proposed_competitor.competitor_brand, brand.id, evidence_repo, run_record_repo=run_record_repo
        )
        brand_claims[proposed_competitor.competitor_brand] = claims
        events_by_brand[proposed_competitor.competitor_brand] = events
        company_by_brand[proposed_competitor.competitor_brand] = proposed_competitor.company

    grid = build_grid(brand_claims)

    # Reconcile each claim's own `strength` with the grid's aggregate view,
    # so a persisted Competitor.claims entry agrees with MessageMap.grid.
    strength_by_driver_brand = {(cell.driver, cell.brand): cell.strength for cell in grid}
    for brand_name, claims in brand_claims.items():
        for claim in claims:
            claim.strength = strength_by_driver_brand[(claim.driver, brand_name)]

    importance = compute_driver_importance(personas)
    whitespace = find_whitespace(grid, importance, personas)
    parity_risks = find_parity_risks(grid, importance, brand.name)

    esov_skipped_reason = None
    threats: list[str] = []
    if sov_by_brand_period and som_by_brand_period:
        for result in compute_esov(sov_by_brand_period, som_by_brand_period):
            if result.flagged:
                threats.append(
                    f"{result.brand} ESOV of {result.esov:+.1f}pts in {result.period} "
                    f"(SOV {result.sov:.1f}% vs SOM {result.som:.1f}%)"
                )
    else:
        esov_skipped_reason = "no share audit / promo audit CSV provided"

    message_map = MessageMap(
        brand_id=brand.id, grid=grid, whitespace=whitespace, parity_risks=parity_risks, threats=threats
    )

    cutoff = date.today() - timedelta(days=RECENT_EVENT_WINDOW_DAYS)
    recent_events = [
        (competitor_brand, event)
        for competitor_brand, events in events_by_brand.items()
        if competitor_brand != brand.name  # threats are about competitors, not us
        for event in events
        if event.date >= cutoff
    ]
    early_warning_signals = _define_early_warning_signals(
        brand, recent_events, run_record_repo=run_record_repo
    )

    competitors = [
        Competitor(
            brand_id=brand.id,
            competitor_brand=competitor_brand,
            company=company_by_brand[competitor_brand],
            claims=claims,
            events=events_by_brand[competitor_brand],
        )
        for competitor_brand, claims in brand_claims.items()
        if competitor_brand != brand.name
    ]

    saved_competitors = CompetitorRepo(session).add_many(competitors)
    saved_message_map = MessageMapRepo(session).add(message_map)
    saved_signals = (
        EarlyWarningSignalRepo(session).add_many(early_warning_signals) if early_warning_signals else []
    )

    return M4Result(
        competitors=saved_competitors,
        message_map=saved_message_map,
        early_warning_signals=saved_signals,
        esov_skipped_reason=esov_skipped_reason,
    )
