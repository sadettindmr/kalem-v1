"""add ezproxy settings

Revision ID: 7245dcd6adc4
Revises: d7f2a3b8c901
Create Date: 2026-03-30 15:36:47.193281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7245dcd6adc4'
down_revision: Union[str, Sequence[str], None] = 'd7f2a3b8c901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user_settings",
        sa.Column("ezproxy_prefix", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "user_settings",
        sa.Column("ezproxy_cookie", sa.String(length=2000), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_settings", "ezproxy_cookie")
    op.drop_column("user_settings", "ezproxy_prefix")
