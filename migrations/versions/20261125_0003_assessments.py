"""Add durable assessment records.

Revision ID: 20261125_0003
Revises: 20261125_0002
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261125_0003"
down_revision = "20261125_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "opportunity_id",
            sa.UUID(),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("rubric_version", sa.String(100), nullable=True),
        sa.Column("cutoff", sa.Integer(), nullable=True),
        sa.Column("result", JSONB(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("model", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assessments_opportunity_id",
        "assessments",
        ["opportunity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_assessments_opportunity_id", table_name="assessments")
    op.drop_table("assessments")
