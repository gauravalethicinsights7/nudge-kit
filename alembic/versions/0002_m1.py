"""M1: evidence.source_category, market_landscape, research_gap

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("source_category", sa.String(40), nullable=True))

    op.create_table(
        "market_landscape",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("patient_funnel", JSONB, nullable=True),
        sa.Column("market_size", JSONB, nullable=True),
        sa.Column("growth_pct", JSONB, nullable=True),
        sa.Column("paradigm", JSONB, nullable=True),
        sa.Column("access_summary", sa.String, nullable=True),
        sa.Column("unmet_needs", JSONB, nullable=False, server_default="[]"),
        sa.Column("key_facts", JSONB, nullable=False, server_default="[]"),
    )

    op.create_table(
        "research_gap",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("block", sa.String(50), nullable=False),
        sa.Column("question", sa.String, nullable=False),
        sa.Column("best_confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("reason", sa.String(20), nullable=False),
        sa.Column("notes", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("research_gap")
    op.drop_table("market_landscape")
    op.drop_column("evidence", "source_category")
