"""initial: pgvector extension, brand, evidence, run_records

Revision ID: 0001
Revises:
Create Date: 2026-09-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "brand",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("molecule", sa.String, nullable=False),
        sa.Column("indication", sa.String, nullable=False),
        sa.Column("market", sa.String(20), nullable=False),
        sa.Column("lifecycle_stage", sa.String(20), nullable=False),
        sa.Column("company", sa.String, nullable=False),
        sa.Column("price_band", sa.String, nullable=True),
        sa.Column("notes", sa.String, nullable=True),
    )

    op.create_table(
        "evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("as_of", sa.Date, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("claim", sa.String(500), nullable=False),
        sa.Column("quote", sa.String, nullable=True),
        sa.Column("source_url", sa.String, nullable=True),
        sa.Column("publisher", sa.String, nullable=True),
        sa.Column("published_date", sa.Date, nullable=True),
        sa.Column("entities_mentioned", JSONB, nullable=False, server_default="[]"),
        sa.Column("mlr_status", sa.String(20), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("normalized_url", sa.String, nullable=True),
        sa.Column("claim_hash", sa.String(64), nullable=False),
    )
    op.create_index("ix_evidence_normalized_url", "evidence", ["normalized_url"])
    op.create_index("ix_evidence_claim_hash", "evidence", ["claim_hash"])

    op.create_table(
        "run_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("inputs_hash", sa.String(64), nullable=False),
        sa.Column("prompt_versions", JSONB, nullable=False, server_default="{}"),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("error", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("run_records")
    op.drop_index("ix_evidence_claim_hash", table_name="evidence")
    op.drop_index("ix_evidence_normalized_url", table_name="evidence")
    op.drop_table("evidence")
    op.drop_table("brand")
    op.execute("DROP EXTENSION IF EXISTS vector")
