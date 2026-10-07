"""M2: adoption_state, segment, target_list

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "adoption_state",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("hcp_id", UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("rung", sa.String(20), nullable=False),
        sa.Column("entered_on", sa.Date, nullable=False),
        sa.Column("p_move_up", sa.Float, nullable=False),
        sa.Column("measured", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("rung_confidence", sa.Float, nullable=False, server_default="1.0"),
    )
    op.create_index("ix_adoption_state_hcp_id", "adoption_state", ["hcp_id"])

    op.create_table(
        "segment",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("rule", JSONB, nullable=False, server_default="{}"),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("hcp_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_potential", sa.Float, nullable=False, server_default="0"),
        sa.Column("avg_share", sa.Float, nullable=False, server_default="0"),
        sa.Column("target_share", sa.Float, nullable=False, server_default="0"),
        sa.Column("intent", sa.String, nullable=True),
        sa.Column("mode", sa.String(20), nullable=False, server_default="hcp_level"),
    )

    op.create_table(
        "target_list",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("segment_id", UUID(as_uuid=True), sa.ForeignKey("segment.id"), nullable=False),
        sa.Column("entries", JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("target_list")
    op.drop_table("segment")
    op.drop_index("ix_adoption_state_hcp_id", table_name="adoption_state")
    op.drop_table("adoption_state")
