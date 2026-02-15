"""add_new_source_types

Revision ID: ea63d692364c
Revises: a1b2c3d4e5f6
Create Date: 2026-02-14 11:03:42.558708

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ea63d692364c'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new source types to source_type enum."""
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'arxiv'")
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'crossref'")
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'core'")


def downgrade() -> None:
    """PostgreSQL does not support removing enum values."""
    pass
