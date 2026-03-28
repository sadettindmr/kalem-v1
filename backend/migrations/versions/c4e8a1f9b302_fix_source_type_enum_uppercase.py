"""fix_source_type_enum_uppercase

Revision ID: c4e8a1f9b302
Revises: b89a4c5f7d23
Create Date: 2026-03-28 21:00:00.000000

Migration fixes:
  ea63d692364c added lowercase values 'arxiv', 'crossref', 'core' but
  SQLAlchemy stores Python enum member NAMES (uppercase) in PostgreSQL
  native enum columns. The initial migration created 'SEMANTIC', 'OPENALEX',
  'MANUAL' (uppercase), so the pattern must be consistent.

  This migration adds the uppercase variants so INSERT statements emitted
  by SQLAlchemy succeed for all SourceType values.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4e8a1f9b302"
down_revision: Union[str, Sequence[str], None] = "b89a4c5f7d23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add uppercase ARXIV, CROSSREF, CORE values to source_type enum.

    ea63d692364c mistakenly added lowercase variants; SQLAlchemy writes
    uppercase names, so this migration adds the correct uppercase values.
    """
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'ARXIV'")
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'CROSSREF'")
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'CORE'")
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'MANUAL'")


def downgrade() -> None:
    """PostgreSQL does not support removing enum values."""
    pass
