"""M4: competitor, message_map, early_warning_signal

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competitor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("competitor_brand", sa.String, nullable=False),
        sa.Column("company", sa.String, nullable=False),
        sa.Column("share_trend", JSONB, nullable=False, server_default="[]"),
        sa.Column("sov", JSONB, nullable=False, server_default="[]"),
        sa.Column("claims", JSONB, nullable=False, server_default="[]"),
        sa.Column("price", JSONB, nullable=True),
        sa.Column("events", JSONB, nullable=False, server_default="[]"),
    )

    op.create_table(
        "message_map",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("grid", JSONB, nullable=False, server_default="[]"),
        sa.Column("whitespace", JSONB, nullable=False, server_default="[]"),
        sa.Column("parity_risks", JSONB, nullable=False, server_default="[]"),
        sa.Column("threats", JSONB, nullable=False, server_default="[]"),
    )

    op.create_table(
        "early_warning_signal",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("detection_rule", sa.String, nullable=False),
        sa.Column("affected_segments", JSONB, nullable=False, server_default="[]"),
        sa.Column("evidence_ids", JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("early_warning_signal")
    op.drop_table("message_map")
    op.drop_table("competitor")
