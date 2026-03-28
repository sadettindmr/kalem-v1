"""add_error_message_to_library_entries

Revision ID: b89a4c5f7d23
Revises: 3c4a09dd9c21
Create Date: 2026-03-28 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b89a4c5f7d23"
down_revision: Union[str, Sequence[str], None] = "3c4a09dd9c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # library_entries tablosuna error_message kolonu ekle
    op.add_column(
        "library_entries",
        sa.Column("error_message", sa.String(length=1000), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # error_message kolonunu kaldır
    op.drop_column("library_entries", "error_message")
