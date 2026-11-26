"""Store claim-to-fact mappings on each immutable draft revision.

Revision ID: 20261125_0005
Revises: 20261125_0004
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261125_0005"
down_revision = "20261125_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "draft_revisions",
        sa.Column("claims", JSONB(), nullable=False, server_default="[]"),
    )
    op.alter_column("draft_revisions", "claims", server_default=None)


def downgrade() -> None:
    op.drop_column("draft_revisions", "claims")
