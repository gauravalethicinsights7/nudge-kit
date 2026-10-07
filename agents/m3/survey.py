"""survey derivation path: cluster raw driver/barrier item ratings (KMeans +
silhouette, standing in for true k-prototypes since this path isn't
fixture-tested this session — see the M3 plan's flagged approximation) -> one
aggregate Evidence row per cluster (the cluster's mean item scores, so
'assumption=False' personas still cite something real and reproducible, not
raw unlinkable numbers) -> finalize.derive_persona per cluster.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from agents.m3.finalize import DerivedPersona, derive_persona
from agents.m3.text_signal import pack_context
from models.clustering import cluster_vectors
from models.evidence import confidence_score
from schemas.base import utcnow
from schemas.brand import Brand
from schemas.enums import EvidenceType, Origin, PersonaDerivation, SourceCategory
from schemas.evidence import Evidence
from schemas.pack import Pack
from store.evidence_repo import EvidenceRepo


class SurveyResponse(BaseModel):
    respondent_id: str
    items: dict[str, float]  # e.g. Likert-scale driver/barrier ratings


def _vectorize(responses: list[SurveyResponse]) -> tuple[list[str], list[list[float]]]:
    item_names = sorted({name for r in responses for name in r.items})
    vectors = [[r.items.get(name, 0.0) for name in item_names] for r in responses]
    return item_names, vectors


def run_survey(
    brand: Brand,
    pack: Pack,
    responses: list[SurveyResponse],
    evidence_repo: EvidenceRepo,
    *,
    run_record_repo=None,
) -> list[DerivedPersona]:
    item_names, vectors = _vectorize(responses)
    clustering = cluster_vectors(vectors)

    clusters: dict[int, list[SurveyResponse]] = {}
    for response, label in zip(responses, clustering.labels):
        clusters.setdefault(label, []).append(response)

    context = pack_context(pack)
    today = utcnow().date()
    derived: list[DerivedPersona] = []
    other_names: list[str] = []

    for members in clusters.values():
        means = {
            name: sum(m.items.get(name, 0.0) for m in members) / len(members) for name in item_names
        }
        summary_text = "; ".join(
            f"{name}: {score:.2f} avg" for name, score in sorted(means.items(), key=lambda kv: -kv[1])
        )
        claim = f"Survey cluster of {len(members)} respondents — {summary_text}"[:500]

        evidence = evidence_repo.add(
            Evidence(
                brand_id=brand.id,
                source="survey_data",
                origin=Origin.internal,
                as_of=today,
                confidence=confidence_score(SourceCategory.other, today, today),
                type=EvidenceType.hcp_insight,
                claim=claim,
                source_category=SourceCategory.other,
            )
        )

        result = derive_persona(
            "derive_persona_from_cluster",
            {
                "brand_name": brand.name,
                "market": brand.market.value,
                "cluster_size": len(members),
                "cluster_summary": f"[{evidence.id}] {claim}",
                "other_persona_names": json.dumps(other_names),
                **context,
            },
            brand,
            pack,
            PersonaDerivation.survey,
            assumption=False,
            confidence=1.0,
            module="m3_survey",
            run_record_repo=run_record_repo,
        )
        other_names.append(result.persona.name)
        derived.append(result)

    return derived
