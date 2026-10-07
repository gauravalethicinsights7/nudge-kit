"""Auth/multi-tenancy + per-object review + async jobs: tenant, app_user,
user_brand_access, review_decision, job

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "app_user",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "user_brand_access",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("granted_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_user_brand_access_unique", "user_brand_access", ["user_id", "brand_id"], unique=True)

    op.create_table(
        "review_decision",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("object_id", UUID(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("comment", sa.String, nullable=True),
        sa.Column("reviewer_user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "job",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brand.id"), nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("message", sa.String, nullable=True),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("error", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("job")
    op.drop_table("review_decision")
    op.drop_table("user_brand_access")
    op.drop_table("app_user")
    op.drop_table("tenant")
