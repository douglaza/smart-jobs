"""Create the initial empty migration baseline.

Revision ID: 20261125_0001
Revises:
Create Date: 2026-11-25
"""

from collections.abc import Sequence

revision: str = "20261125_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
