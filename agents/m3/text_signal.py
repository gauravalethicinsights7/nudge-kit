"""Shared 'extract claims from free text -> embed -> cluster -> finalize
persona' pipeline for the call_notes and social derivation paths — both
cluster embeddings of LLM-extracted claims from text (call notes / posts),
per specs/m3-personas.md ('social: same as call_notes on HCP posts').

Extracted claims are persisted as Evidence (type=hcp_insight, origin=internal,
source_category=other — internal rep/CRM signal doesn't fit the public-source
categories models/evidence.py's confidence_score was built around, so it gets
the same 0.5-base 'other' bucket used for ambiguous cases), reusing M1's
EvidenceRepo/confidence_score exactly as-is.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from uuid import UUID, uuid5

from pydantic import BaseModel, Field

from agents.m3.finalize import DerivedPersona, derive_persona
from llm.client import call
from models.clustering import cluster_vectors
from models.evidence import confidence_score
from schemas.base import utcnow
from schemas.brand import Brand
from schemas.enums import EvidenceType, Origin, PersonaDerivation, SourceCategory
from schemas.evidence import Evidence
from schemas.pack import Pack
from schemas.persona_assignment import PersonaAssignment
from store.embeddings import embed_text
from store.evidence_repo import EvidenceRepo

PROMPTS_DIR = Path(__file__).parent / "prompts"
HCP_REF_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # fixed, arbitrary — RFC 4122 example NS


class TextSignalItem(BaseModel):
    item_id: str
    hcp_ref: str | None = None  # crm_id or similar stable external identifier, if known
    text: str


class ExtractedClaims(BaseModel):
    claims: list[str] = Field(default_factory=list)


def pack_context(pack: Pack) -> dict:
    return {
        "pack_channels": json.dumps([{"id": c.id, "name": c.name} for c in pack.channels]),
        "pack_signals": json.dumps(pack.signals),
    }


def _extract_item(
    item: TextSignalItem,
    brand: Brand,
    evidence_repo: EvidenceRepo,
    source_prefix: str,
    run_record_repo=None,
) -> list[Evidence]:
    result = call(
        "extract_text_signal",
        {"text": item.text},
        ExtractedClaims,
        model_tier="standard",
        module=f"m3_{source_prefix}_extract",
        run_record_repo=run_record_repo,
        prompts_dir=PROMPTS_DIR,
    )
    today = utcnow().date()
    saved = []
    for claim_text in result.claims:
        evidence = Evidence(
            brand_id=brand.id,
            source=f"{source_prefix}:{item.item_id}",
            origin=Origin.internal,
            as_of=today,
            confidence=confidence_score(SourceCategory.other, today, today),
            type=EvidenceType.hcp_insight,
            claim=claim_text,
            source_category=SourceCategory.other,
        )
        saved.append(evidence_repo.add(evidence))
    return saved


def run_text_signal_derivation(
    brand: Brand,
    pack: Pack,
    items: list[TextSignalItem],
    evidence_repo: EvidenceRepo,
    derivation: PersonaDerivation,
    source_prefix: str,
    *,
    run_record_repo=None,
) -> tuple[list[DerivedPersona], list[PersonaAssignment]]:
    evidence_by_item = {
        item.item_id: _extract_item(item, brand, evidence_repo, source_prefix, run_record_repo)
        for item in items
    }

    # An item with no extractable signal can't be embedded meaningfully.
    usable_items = [i for i in items if evidence_by_item[i.item_id]]
    embeddings = [
        embed_text(" ".join(e.claim for e in evidence_by_item[i.item_id])) for i in usable_items
    ]
    clustering = cluster_vectors(embeddings)

    items_by_cluster: dict[int, list[TextSignalItem]] = defaultdict(list)
    for item, label in zip(usable_items, clustering.labels):
        items_by_cluster[label].append(item)

    context = pack_context(pack)
    derived: list[DerivedPersona] = []
    other_names: list[str] = []
    persona_by_cluster: dict[int, UUID] = {}

    for cluster_id, cluster_items in items_by_cluster.items():
        cluster_evidence = [e for i in cluster_items for e in evidence_by_item[i.item_id]]
        cluster_summary = "\n".join(f"[{e.id}] {e.claim}" for e in cluster_evidence)

        result = derive_persona(
            "derive_persona_from_cluster",
            {
                "brand_name": brand.name,
                "market": brand.market.value,
                "cluster_size": len(cluster_items),
                "cluster_summary": cluster_summary[:12000],
                "other_persona_names": json.dumps(other_names),
                **context,
            },
            brand,
            pack,
            derivation,
            assumption=False,
            confidence=1.0,
            module=f"m3_{source_prefix}_finalize",
            run_record_repo=run_record_repo,
        )
        other_names.append(result.persona.name)
        derived.append(result)
        persona_by_cluster[cluster_id] = result.persona.id

    hcp_cluster_votes: dict[str, list[int]] = defaultdict(list)
    for item, label in zip(usable_items, clustering.labels):
        if item.hcp_ref:
            hcp_cluster_votes[item.hcp_ref].append(label)

    assignments = []
    for hcp_ref, votes in hcp_cluster_votes.items():
        majority_cluster, count = Counter(votes).most_common(1)[0]
        assignments.append(
            PersonaAssignment(
                hcp_id=uuid5(HCP_REF_NAMESPACE, hcp_ref),
                brand_id=brand.id,
                persona_id=persona_by_cluster[majority_cluster],
                confidence=count / len(votes),
            )
        )

    return derived, assignments
