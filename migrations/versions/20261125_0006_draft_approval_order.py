"""Order successive decisions on a draft revision.

Revision ID: 20261125_0006
Revises: 20261125_0005
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op

revision = "20261125_0006"
down_revision = "20261125_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "draft_approvals",
        sa.Column("decision_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_unique_constraint(
        "uq_draft_approval_decision_number",
        "draft_approvals",
        ["revision_id", "decision_number"],
    )
    op.alter_column("draft_approvals", "decision_number", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "uq_draft_approval_decision_number",
        "draft_approvals",
        type_="unique",
    )
    op.drop_column("draft_approvals", "decision_number")
