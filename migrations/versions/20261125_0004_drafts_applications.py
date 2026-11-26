"""Add immutable draft revisions and manual application history.

Revision ID: 20261125_0004
Revises: 20261125_0003
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261125_0004"
down_revision = "20261125_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "opportunity_id",
            sa.UUID(),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_drafts_opportunity_id", "drafts", ["opportunity_id"])

    op.create_table(
        "draft_revisions",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "draft_id",
            sa.UUID(),
            sa.ForeignKey("drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("fact_ids", JSONB(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("draft_id", "version", name="uq_draft_revision_version"),
    )
    op.create_index(
        "ix_draft_revisions_draft_id",
        "draft_revisions",
        ["draft_id"],
    )

    op.create_table(
        "draft_approvals",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "revision_id",
            sa.UUID(),
            sa.ForeignKey("draft_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_draft_approvals_revision_id",
        "draft_approvals",
        ["revision_id"],
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "opportunity_id",
            sa.UUID(),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "draft_revision_id",
            sa.UUID(),
            sa.ForeignKey("draft_revisions.id"),
            nullable=True,
        ),
        sa.Column("state", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("opportunity_id", name="uq_applications_opportunity"),
    )

    op.create_table(
        "application_events",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "application_id",
            sa.UUID(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_state", sa.String(30), nullable=True),
        sa.Column("to_state", sa.String(30), nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("confirmation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_application_events_application_id",
        "application_events",
        ["application_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_events_application_id", table_name="application_events"
    )
    op.drop_table("application_events")
    op.drop_table("applications")
    op.drop_index("ix_draft_approvals_revision_id", table_name="draft_approvals")
    op.drop_table("draft_approvals")
    op.drop_index("ix_draft_revisions_draft_id", table_name="draft_revisions")
    op.drop_table("draft_revisions")
    op.drop_index("ix_drafts_opportunity_id", table_name="drafts")
    op.drop_table("drafts")
