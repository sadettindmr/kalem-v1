"""add_pdf_url_to_papers

Revision ID: a1b2c3d4e5f6
Revises: 74a35bd4d28c
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '74a35bd4d28c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pdf_url column to papers table."""
    op.add_column('papers', sa.Column('pdf_url', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    """Remove pdf_url column from papers table."""
    op.drop_column('papers', 'pdf_url')
