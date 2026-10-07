from __future__ import annotations

from uuid import UUID

from pydantic import Field, model_validator

from schemas.base import Base, StrictModel
from schemas.enums import Driver, EvidenceType, PersonaDerivation, Rung

REQUIRED_BARRIER_RUNGS = {Rung.aware, Rung.considering, Rung.trialist}


class Persona(Base):
    brand_id: UUID
    name: str
    beliefs: list[str] = Field(default_factory=list)
    drivers_ranked: list[Driver] = Field(default_factory=list)
    barriers_by_rung: dict[Rung, list[str]] = Field(default_factory=dict)
    evidence_needs: list[EvidenceType] = Field(default_factory=list)
    channel_affinity: dict[str, float] = Field(default_factory=dict)
    influence_network: list[str] = Field(default_factory=list)
    share_of_universe: float = Field(ge=0.0, le=1.0)
    share_of_potential: float = Field(ge=0.0, le=1.0)
    derivation: PersonaDerivation
    evidence_ids: list[UUID] = Field(default_factory=list)
    # specs/m3-personas.md's synthetic path: "every field assumption=True;
    # confidence <= 0.4". Persona-level, not per-field/per-driver — no finer
    # grained evidence structure exists anywhere else in this schema.
    assumption: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)

    @model_validator(mode="after")
    def _check_drivers_ranked_is_full_permutation(self) -> "Persona":
        """specs/m3-personas.md: 'drivers_ranked: exactly the Driver enum, ranked.'"""
        if set(self.drivers_ranked) != set(Driver):
            raise ValueError(
                f"drivers_ranked must rank every Driver exactly once; "
                f"got {[d.value for d in self.drivers_ranked]}"
            )
        return self

    @model_validator(mode="after")
    def _check_barriers_cover_required_rungs(self) -> "Persona":
        """specs/m3-personas.md: 'barriers_by_rung: at least aware->considering,
        considering->trialist, trialist->adopter' (keyed by the from-rung)."""
        if not REQUIRED_BARRIER_RUNGS.issubset(self.barriers_by_rung):
            missing = REQUIRED_BARRIER_RUNGS - set(self.barriers_by_rung)
            raise ValueError(f"barriers_by_rung is missing required rungs: {sorted(r.value for r in missing)}")
        return self

    @model_validator(mode="after")
    def _check_evidence_or_assumption(self) -> "Persona":
        """specs/m3-personas.md: top drivers 'justified with evidence_ids or
        marked assumption' — persona-level: a non-assumption persona must cite
        some evidence."""
        if not self.assumption and not self.evidence_ids:
            raise ValueError("a non-assumption persona must have at least one evidence_id")
        return self


class JourneyStep(StrictModel):
    from_rung: Rung
    to_rung: Rung
    job: str
    barrier: str
    proof: str
    lead_channels: list[str] = Field(default_factory=list)
    exit_signal: str


class JourneyMap(Base):
    brand_id: UUID
    persona_id: UUID | None = None
    steps: list[JourneyStep] = Field(default_factory=list)
