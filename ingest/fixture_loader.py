"""Loads a fixtures/<name>.yaml worked example into Brand (+ optionally seed
Evidence for the Foundations dummy eval).

`build_brand_from_fixture` is the shared piece: it just builds the Brand
object from the fixture's `brand:` block, used both by `load_fixture` below
(which also seeds `known_facts` as Evidence, for Foundations' dummy eval) and
by M1's fixture runner, which must NOT pre-seed its own answers — M1 has to
discover evidence independently via real web research, or the M1 eval
(matching persisted Evidence against these same known_facts) is meaningless.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from schemas.brand import Brand
from schemas.enums import EvidenceType, LifecycleStage, Market, Origin
from schemas.evidence import Evidence
from store.brand_repo import BrandRepo
from store.evidence_repo import EvidenceRepo

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture_data(fixture_name: str) -> dict:
    path = FIXTURES_DIR / f"{fixture_name}.yaml"
    return yaml.safe_load(path.read_text())


def build_brand_from_fixture(fixture_name: str) -> Brand:
    brand_data = load_fixture_data(fixture_name)["brand"]
    return Brand(
        name=brand_data["name"],
        molecule=brand_data["molecule"],
        indication=brand_data["indication"],
        market=Market(brand_data["market"]),
        lifecycle_stage=LifecycleStage(brand_data["lifecycle_stage"]),
        company=brand_data["company"],
        price_band=brand_data.get("price_band"),
    )


def load_fixture(session: Session, fixture_name: str) -> tuple[Brand, list[Evidence]]:
    data = load_fixture_data(fixture_name)
    saved_brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))

    evidence_repo = EvidenceRepo(session)
    saved_evidence = []
    for fact in data.get("known_facts", []):
        evidence = Evidence(
            brand_id=saved_brand.id,
            source="fixture:known_facts",
            origin=Origin.external,
            as_of=date.today(),
            confidence=0.8,
            type=EvidenceType.market,
            claim=fact["fact"],
            source_url=fact.get("source"),
        )
        saved_evidence.append(evidence_repo.add(evidence))

    return saved_brand, saved_evidence
