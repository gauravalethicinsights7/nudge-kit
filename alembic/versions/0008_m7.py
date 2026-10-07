"""M7: content_module, journey_rule, action

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_module",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("channel_refs", JSONB, nullable=False, server_default="[]"),
        sa.Column("driver", sa.String(50), nullable=False),
        sa.Column("persona_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("claim", sa.String, nullable=False),
        sa.Column("evidence_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("format", sa.String, nullable=False),
        sa.Column("mlr_status", sa.String(20), nullable=False, server_default="none"),
        sa.Column("on_label", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_comparative", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("comparative_approved", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("patient_directed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("exceeds_pack_limit", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "journey_rule",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("segment_id", UUID(as_uuid=True), nullable=False),
        sa.Column("persona_id", UUID(as_uuid=True), nullable=False),
        sa.Column("entry_criteria", JSONB, nullable=False, server_default="{}"),
        sa.Column("steps", JSONB, nullable=False, server_default="[]"),
        sa.Column("escalation", JSONB, nullable=False, server_default="[]"),
        sa.Column("exit_signal", sa.String, nullable=False),
    )

    op.create_table(
        "action",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("hcp_id", UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("content_ref", sa.String, nullable=True),
        sa.Column("suggested_date", sa.Date, nullable=False),
        sa.Column("reason", sa.String, nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("action_status", sa.String(20), nullable=False, server_default="suggested"),
    )


def downgrade() -> None:
    op.drop_table("action")
    op.drop_table("journey_rule")
    op.drop_table("content_module")
