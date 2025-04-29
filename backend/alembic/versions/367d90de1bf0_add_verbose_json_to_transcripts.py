"""add verbose_json to transcripts

Revision ID: 367d90de1bf0
Revises: 7192b9e3f6d9
Create Date: 2025-04-29 08:38:45.648543
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql  # ← ★ 追加

# revision identifiers, used by Alembic.
revision: str = "367d90de1bf0"
down_revision: Union[str, None] = "7192b9e3f6d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add verbose_json column."""
    op.add_column(
        "transcripts",
        sa.Column(
            "verbose_json",
            postgresql.JSON(astext_type=sa.Text()),  # JSON でも JSONB でも可
            nullable=True,
        ),
        schema="minutes",
    )


def downgrade() -> None:
    """Downgrade schema by dropping verbose_json column."""
    op.drop_column("transcripts", "verbose_json", schema="minutes")
