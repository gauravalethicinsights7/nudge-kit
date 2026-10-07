"""synthetic derivation path: no real respondent data — the LLM hypothesises
personas from literature/market context. specs/m3-personas.md: 'every field
assumption=True; confidence <= 0.4.'
"""

from __future__ import annotations

import json

from agents.m3.finalize import DerivedPersona, derive_persona
from agents.m3.text_signal import pack_context
from schemas.brand import Brand
from schemas.enums import PersonaDerivation
from schemas.market_landscape import MarketLandscape
from schemas.pack import Pack

SYNTHETIC_CONFIDENCE = 0.4  # spec: "confidence <= 0.4"
DEFAULT_PERSONA_COUNT = 4


def run_synthetic(
    brand: Brand,
    pack: Pack,
    market_landscape: MarketLandscape | None = None,
    persona_count: int = DEFAULT_PERSONA_COUNT,
    *,
    run_record_repo=None,
) -> list[DerivedPersona]:
    landscape_summary = (
        json.dumps(market_landscape.model_dump(mode="json"), default=str)
        if market_landscape
        else "none available"
    )
    context = pack_context(pack)

    derived: list[DerivedPersona] = []
    other_names: list[str] = []

    for i in range(persona_count):
        result = derive_persona(
            "derive_persona_synthetic",
            {
                "brand_name": brand.name,
                "market": brand.market.value,
                "persona_index": i + 1,
                "persona_count": persona_count,
                "market_landscape_summary": landscape_summary,
                "other_persona_names": json.dumps(other_names),
                **context,
            },
            brand,
            pack,
            PersonaDerivation.synthetic,
            assumption=True,
            confidence=SYNTHETIC_CONFIDENCE,
            module="m3_synthetic",
            run_record_repo=run_record_repo,
        )
        other_names.append(result.persona.name)
        derived.append(result)

    return derived
