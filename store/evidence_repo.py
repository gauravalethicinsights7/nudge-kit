from __future__ import annotations

import hashlib
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import EvidenceType, MlrStatus, Origin, SourceCategory, Status
from schemas.evidence import Evidence
from store.embeddings import embed_text
from store.orm import EvidenceORM


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip().lower()
    url = re.sub(r"^https?://(www\.)?", "", url)
    return url.rstrip("/")


def claim_hash(claim: str) -> str:
    normalized = re.sub(r"\s+", " ", claim.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()


def _to_orm(evidence: Evidence) -> EvidenceORM:
    return EvidenceORM(
        id=evidence.id,
        tenant_id=evidence.tenant_id,
        created_at=evidence.created_at,
        updated_at=evidence.updated_at,
        status=evidence.status.value,
        version=evidence.version,
        source=evidence.source,
        origin=evidence.origin.value,
        as_of=evidence.as_of,
        confidence=evidence.confidence,
        brand_id=evidence.brand_id,
        type=evidence.type.value,
        claim=evidence.claim,
        quote=evidence.quote,
        source_url=evidence.source_url,
        publisher=evidence.publisher,
        published_date=evidence.published_date,
        entities_mentioned=evidence.entities_mentioned,
        mlr_status=evidence.mlr_status.value,
        embedding=evidence.embedding or embed_text(evidence.claim),
        source_category=evidence.source_category.value if evidence.source_category else None,
        normalized_url=normalize_url(evidence.source_url),
        claim_hash=claim_hash(evidence.claim),
    )


def _to_pydantic(row: EvidenceORM) -> Evidence:
    return Evidence(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        source=row.source,
        origin=Origin(row.origin),
        as_of=row.as_of,
        confidence=row.confidence,
        brand_id=row.brand_id,
        type=EvidenceType(row.type),
        claim=row.claim,
        quote=row.quote,
        source_url=row.source_url,
        publisher=row.publisher,
        published_date=row.published_date,
        entities_mentioned=row.entities_mentioned or [],
        mlr_status=MlrStatus(row.mlr_status),
        embedding=list(row.embedding) if row.embedding is not None else None,
        source_category=SourceCategory(row.source_category) if row.source_category else None,
    )


class EvidenceRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, evidence: Evidence) -> Evidence:
        """Insert, or return the existing row if (brand_id, normalized_url, claim_hash)
        already exists — de-duplication per specs/00-foundations.md."""
        row = _to_orm(evidence)
        existing = self.session.scalars(
            select(EvidenceORM).where(
                EvidenceORM.brand_id == row.brand_id,
                EvidenceORM.claim_hash == row.claim_hash,
                EvidenceORM.normalized_url.is_(row.normalized_url)
                if row.normalized_url is None
                else EvidenceORM.normalized_url == row.normalized_url,
            )
        ).first()
        if existing is not None:
            return _to_pydantic(existing)

        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def search(
        self,
        query: str,
        brand_id: UUID,
        types: list[EvidenceType] | None = None,
        k: int = 10,
    ) -> list[Evidence]:
        query_vec = embed_text(query)
        stmt = select(EvidenceORM).where(EvidenceORM.brand_id == brand_id)
        if types:
            stmt = stmt.where(EvidenceORM.type.in_([t.value for t in types]))
        stmt = stmt.order_by(EvidenceORM.embedding.cosine_distance(query_vec)).limit(k)
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]

    def get_many(self, ids: list[UUID]) -> list[Evidence]:
        if not ids:
            return []
        rows = self.session.scalars(select(EvidenceORM).where(EvidenceORM.id.in_(ids))).all()
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(
        self, brand_id: UUID, types: list[EvidenceType] | None = None
    ) -> list[Evidence]:
        stmt = select(EvidenceORM).where(EvidenceORM.brand_id == brand_id)
        if types:
            stmt = stmt.where(EvidenceORM.type.in_([t.value for t in types]))
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]
