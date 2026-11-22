"""add priority to reports

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
    )
    op.create_index("ix_reports_priority", "reports", ["priority"], unique=False)
    # Backfill existing rows from category:
    #   TRAPPED (2) -> 1, FIRE (3) -> 1, MEDICAL (1) -> 2, everything else -> 3
    op.execute("UPDATE reports SET priority = 1 WHERE category IN (2, 3)")
    op.execute("UPDATE reports SET priority = 2 WHERE category = 1")
    # rows not matching the above already have the default of 3


def downgrade() -> None:
    op.drop_index("ix_reports_priority", table_name="reports")
    op.drop_column("reports", "priority")
