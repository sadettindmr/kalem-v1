"""add_user_settings_table

Revision ID: 3c4a09dd9c21
Revises: f13a1c9d0b77
Create Date: 2026-02-15 23:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3c4a09dd9c21"
down_revision: Union[str, Sequence[str], None] = "f13a1c9d0b77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("openai_api_key", sa.String(length=500), nullable=True),
        sa.Column("semantic_scholar_api_key", sa.String(length=500), nullable=True),
        sa.Column("core_api_key", sa.String(length=500), nullable=True),
        sa.Column("openalex_email", sa.String(length=255), nullable=True),
        sa.Column(
            "enabled_providers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                '\'["semantic","openalex","arxiv","crossref","core"]\'::jsonb'
            ),
        ),
        sa.Column(
            "proxy_url",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "proxy_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_settings")

