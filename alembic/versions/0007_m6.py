"""M6: channel, channel_fit, channel_plan

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("channel_ref", sa.String(50), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("unit", sa.String, nullable=False),
        sa.Column("unit_cost", JSONB, nullable=True),
        sa.Column("capacity", sa.Float, nullable=True),
        sa.Column("stage_fit", JSONB, nullable=False, server_default="{}"),
        sa.Column("curve", JSONB, nullable=False),
        sa.Column("compliance_rule_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("diagnostics", JSONB, nullable=True),
    )

    op.create_table(
        "channel_fit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("segment_id", UUID(as_uuid=True), nullable=False),
        sa.Column("persona_id", UUID(as_uuid=True), nullable=True),
        sa.Column("channel_id", sa.String(50), nullable=False),
        sa.Column("fit_score", sa.Float, nullable=False),
        sa.Column("components", JSONB, nullable=False),
    )

    op.create_table(
        "channel_plan",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("allocations", JSONB, nullable=False, server_default="{}"),
        sa.Column("sequence_template_ref", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("channel_plan")
    op.drop_table("channel_fit")
    op.drop_table("channel")
