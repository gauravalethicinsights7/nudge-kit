"""Shared 'LLM names/describes a persona' step used by all four derivation
paths (survey/call_notes/social/synthetic). One call produces both the
persona fields and its JourneyMap steps together, since journey content
naturally reuses the same barriers.

channel_affinity / lead_channels / exit_signal are checked against the active
pack via llm.client.call's validation_context — the same mechanism M1's
synthesiser used for evidence_ids — so a hallucinated channel or signal is a
validation error that retries, not a silent bad output (CLAUDE.md rule 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, model_validator

from llm.client import call
from schemas.brand import Brand
from schemas.enums import Driver, EvidenceType, PersonaDerivation, Rung
from schemas.pack import Pack
from schemas.persona import JourneyMap, JourneyStep, Persona

PROMPTS_DIR = Path(__file__).parent / "prompts"


class JourneyStepDraft(BaseModel):
    from_rung: Rung
    to_rung: Rung
    job: str
    barrier: str
    proof: str
    lead_channels: list[str] = Field(default_factory=list)
    exit_signal: str


class PersonaDraft(BaseModel):
    name: str
    beliefs: list[str] = Field(default_factory=list)
    drivers_ranked: list[Driver]
    barriers_by_rung: dict[Rung, list[str]]
    evidence_needs: list[EvidenceType] = Field(default_factory=list)
    channel_affinity: dict[str, float]
    influence_network: list[str] = Field(default_factory=list)
    # Raw, unnormalized relative size signal (e.g. cluster size or the LLM's
    # own judgment of relative importance) — agents/m3/agent.py normalizes
    # this across all personas from one run into share_of_universe.
    relative_weight: float = Field(gt=0.0)
    evidence_ids: list[UUID] = Field(default_factory=list)
    journey_steps: list[JourneyStepDraft]

    @model_validator(mode="after")
    def _check_against_pack(self, info: ValidationInfo) -> "PersonaDraft":
        context = info.context or {}
        pack_channel_ids = context.get("pack_channel_ids")
        pack_signals = context.get("pack_signals")

        if pack_channel_ids is not None:
            if set(self.channel_affinity) != set(pack_channel_ids):
                raise ValueError(
                    "channel_affinity must cover exactly the active pack's channels; "
                    f"got {sorted(self.channel_affinity)}, expected {sorted(pack_channel_ids)}"
                )
            for step in self.journey_steps:
                unknown = set(step.lead_channels) - set(pack_channel_ids)
                if unknown:
                    raise ValueError(f"journey step lead_channels not in pack: {sorted(unknown)}")

        if pack_signals is not None:
            for step in self.journey_steps:
                if step.exit_signal not in pack_signals:
                    raise ValueError(
                        f"journey step exit_signal '{step.exit_signal}' not in pack signals"
                    )

        return self


@dataclass
class DerivedPersona:
    persona: Persona
    journey_map: JourneyMap
    raw_weight: float


def derive_persona(
    prompt_id: str,
    variables: dict,
    brand: Brand,
    pack: Pack,
    derivation: PersonaDerivation,
    *,
    assumption: bool,
    confidence: float,
    module: str,
    run_record_repo=None,
) -> DerivedPersona:
    draft = call(
        prompt_id,
        variables,
        PersonaDraft,
        model_tier="standard",
        module=module,
        run_record_repo=run_record_repo,
        validation_context={
            "pack_channel_ids": {c.id for c in pack.channels},
            "pack_signals": set(pack.signals),
        },
        prompts_dir=PROMPTS_DIR,
    )

    persona = Persona(
        brand_id=brand.id,
        name=draft.name,
        beliefs=draft.beliefs,
        drivers_ranked=draft.drivers_ranked,
        barriers_by_rung=draft.barriers_by_rung,
        evidence_needs=draft.evidence_needs,
        channel_affinity=draft.channel_affinity,
        influence_network=draft.influence_network,
        share_of_universe=0.0,  # placeholder — normalized across the whole run in agent.py
        share_of_potential=0.0,
        derivation=derivation,
        evidence_ids=draft.evidence_ids,
        assumption=assumption,
        confidence=confidence,
    )
    journey_map = JourneyMap(
        brand_id=brand.id,
        persona_id=persona.id,
        steps=[JourneyStep(**step.model_dump()) for step in draft.journey_steps],
    )
    return DerivedPersona(persona=persona, journey_map=journey_map, raw_weight=draft.relative_weight)
