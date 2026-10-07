"""M5: brand_plan

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_plan",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("plan_horizon_months", sa.Integer, nullable=False, server_default="12"),
        sa.Column("situation", JSONB, nullable=False),
        sa.Column("key_issues", JSONB, nullable=False, server_default="[]"),
        sa.Column("imperatives", JSONB, nullable=False, server_default="[]"),
        sa.Column("positioning", JSONB, nullable=False),
        sa.Column("message_house", JSONB, nullable=False),
        sa.Column("objectives", JSONB, nullable=False, server_default="[]"),
        sa.Column("strategies_tactics", JSONB, nullable=False, server_default="[]"),
        sa.Column("kpi_tree", JSONB, nullable=False),
        sa.Column("forecast", JSONB, nullable=False),
        sa.Column("budget", JSONB, nullable=False, server_default="{}"),
        sa.Column("risks_tests", JSONB, nullable=False, server_default="[]"),
        sa.Column("compliance_flags", JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("brand_plan")
