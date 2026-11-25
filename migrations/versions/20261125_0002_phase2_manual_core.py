"""Add manual profile, preference and opportunity tables.

Revision ID: 20261125_0002
Revises: 20261125_0001
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261125_0002"
down_revision = "20261125_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("consented", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "profile_facts",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("fact", sa.Text(), nullable=False),
        sa.Column("source", sa.String(500), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "preferences",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("roles", JSONB(), nullable=False, server_default="[]"),
        sa.Column("seniorities", JSONB(), nullable=False, server_default="[]"),
        sa.Column("modalities", JSONB(), nullable=False, server_default="[]"),
        sa.Column("locations", JSONB(), nullable=False, server_default="[]"),
        sa.Column("salary_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_currency", sa.String(3), nullable=True),
        sa.Column("salary_period", sa.String(20), nullable=True),
        sa.Column("salary_regime", sa.String(20), nullable=True),
        sa.Column("cutoff", sa.Integer(), nullable=True),
        sa.Column("eliminatory_criteria", JSONB(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "opportunities",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("company", sa.String(300), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("modality", sa.String(30), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("salary_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_period", sa.String(20), nullable=True),
        sa.Column("salary_regime", sa.String(20), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_opportunities_fingerprint"),
    )
    op.create_index("ix_opportunities_state", "opportunities", ["state"])
    op.create_index("ix_opportunities_created_at", "opportunities", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_opportunities_created_at", table_name="opportunities")
    op.drop_index("ix_opportunities_state", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_table("preferences")
    op.drop_table("profile_facts")
    op.drop_table("profiles")
