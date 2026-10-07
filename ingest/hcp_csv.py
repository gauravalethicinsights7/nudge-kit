"""CSV -> HCP[] ingest, per CLAUDE.md's /ingest layout ('data adapters (csv
first, API later) -> entities'). Skips '#'-prefixed header-comment lines, the
convention scripts/generate_hcp_fixture.py writes its documentation in.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import NAMESPACE_DNS, UUID, uuid5

import pandas as pd

from ingest.csv_utils import read_csv_skipping_comments
from models.scores import resolve_potential
from schemas.base import ProvNumber
from schemas.enums import Access, Origin, Setting
from schemas.hcp import HCP, Consent, ExternalIds, Geo
from schemas.pack import Pack

# HCP has no persistence layer (no repo exists — see CLAUDE.md's open
# architecture decisions), so every module that needs the "same" HCP across
# separate loads (e.g. M2 building AdoptionState, M7 later matching those
# AdoptionStates to freshly-reloaded HCPs in a later request) needs a stable
# id. Base.id defaults to a random uuid4 per construction, which breaks that
# across repeated CSV loads of the identical row. Deriving id deterministically
# from crm_id (a uuid5, not random) fixes this without adding a repo.
_HCP_ID_NAMESPACE = uuid5(NAMESPACE_DNS, "nudge-kit.hcp")


def _hcp_id_for_crm_id(crm_id: str) -> UUID:
    return uuid5(_HCP_ID_NAMESPACE, crm_id)


def load_hcp_csv(path: Path | str, pack: Pack, as_of: date | None = None) -> list[HCP]:
    path = Path(path)
    as_of = as_of or date.today()
    df = read_csv_skipping_comments(path)

    hcps: list[HCP] = []
    for _, row in df.iterrows():
        hcp = HCP(
            id=_hcp_id_for_crm_id(str(row["crm_id"])),
            external_ids=ExternalIds(crm_id=str(row["crm_id"])),
            name_hash=str(row["crm_id"]),  # synthetic fixture has no real name to hash
            specialty=row["specialty"],
            setting=Setting(row["setting"]),
            geo=Geo(
                state=row.get("state"),
                city=row.get("city"),
                city_tier=row.get("city_tier"),
                territory_id=row.get("territory_id"),
            ),
            # No measured Rx/category volume in this synthetic CSV — placeholder
            # origin=estimated so resolve_potential() below always recomputes it.
            potential=ProvNumber(
                value=0.0, source="unresolved", origin=Origin.estimated, as_of=as_of, confidence=0.0
            ),
            brand_share=ProvNumber(
                value=0.0, source="no data", origin=Origin.estimated, as_of=as_of, confidence=0.0
            ),
            access=Access(row["access"]),
            consent=Consent(
                email=bool(row.get("consent_email", False)),
                whatsapp=bool(row.get("consent_whatsapp", False)),
            ),
            patient_volume_estimate=(
                float(row["patient_volume_estimate"])
                if pd.notna(row.get("patient_volume_estimate"))
                else None
            ),
            rep_class=row.get("rep_class") if pd.notna(row.get("rep_class")) else None,
        )
        hcp.potential = resolve_potential(hcp, pack.potential_proxies, as_of)
        hcps.append(hcp)

    return hcps
