"""M8: engagement_event, outcome, scorecard, lift_estimate, prior_update, assumption_review

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engagement_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("hcp_id", UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("depth", sa.String(50), nullable=False),
        sa.Column("occurred_at", sa.Date, nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
    )

    op.create_table(
        "outcome",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("hcp_id", UUID(as_uuid=True), nullable=True),
        sa.Column("segment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("engagement_index", sa.Float, nullable=False),
        sa.Column("rung", sa.String(20), nullable=True),
        sa.Column("nrx", sa.Float, nullable=True),
        sa.Column("trx", sa.Float, nullable=True),
    )

    op.create_table(
        "scorecard",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("kpis", JSONB, nullable=False, server_default="[]"),
    )

    op.create_table(
        "lift_estimate",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("test_name", sa.String, nullable=False),
        sa.Column("effect", sa.Float, nullable=False),
        sa.Column("ci_low", sa.Float, nullable=False),
        sa.Column("ci_high", sa.Float, nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
    )

    op.create_table(
        "prior_update",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("prior_type", sa.String(30), nullable=False),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("before", sa.Float, nullable=False),
        sa.Column("after", sa.Float, nullable=False),
    )
    op.create_index(
        "ix_prior_update_identity", "prior_update", ["brand_id", "prior_type", "key", "period"], unique=True
    )

    op.create_table(
        "assumption_review",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("items", JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("assumption_review")
    op.drop_table("prior_update")
    op.drop_table("lift_estimate")
    op.drop_table("scorecard")
    op.drop_table("outcome")
    op.drop_table("engagement_event")
