"""uploads: move Data Hub files from disk into the database

Hosts with an ephemeral filesystem (Hugging Face Spaces, most container PaaS)
lose /app/var/uploads on every restart. The engine re-reads those files on
each module run, so losing them silently breaks M2/M6/M7/M8.

Revision ID: 0011
Revises: 0010
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "upload",
        sa.Column("brand_id", sa.UUID(as_uuid=True), sa.ForeignKey("brand.id"), primary_key=True),
        sa.Column("kind", sa.String(50), primary_key=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("upload")
