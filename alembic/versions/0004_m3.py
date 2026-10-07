"""M3: persona, journey_map, persona_assignment

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "persona",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("beliefs", JSONB, nullable=False, server_default="[]"),
        sa.Column("drivers_ranked", JSONB, nullable=False, server_default="[]"),
        sa.Column("barriers_by_rung", JSONB, nullable=False, server_default="{}"),
        sa.Column("evidence_needs", JSONB, nullable=False, server_default="[]"),
        sa.Column("channel_affinity", JSONB, nullable=False, server_default="{}"),
        sa.Column("influence_network", JSONB, nullable=False, server_default="[]"),
        sa.Column("share_of_universe", sa.Float, nullable=False),
        sa.Column("share_of_potential", sa.Float, nullable=False),
        sa.Column("derivation", sa.String(20), nullable=False),
        sa.Column("evidence_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("assumption", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
    )

    op.create_table(
        "journey_map",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("persona_id", UUID(as_uuid=True), sa.ForeignKey("persona.id"), nullable=True),
        sa.Column("steps", JSONB, nullable=False, server_default="[]"),
    )

    op.create_table(
        "persona_assignment",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("hcp_id", UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("persona_id", UUID(as_uuid=True), sa.ForeignKey("persona.id"), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
    )
    op.create_index("ix_persona_assignment_hcp_id", "persona_assignment", ["hcp_id"])


def downgrade() -> None:
    op.drop_index("ix_persona_assignment_hcp_id", table_name="persona_assignment")
    op.drop_table("persona_assignment")
    op.drop_table("journey_map")
    op.drop_table("persona")
