"""add minutes.messages table

Revision ID: f0d0800ada2a
Revises: cf7fba3cd1dd
Create Date: 2025-04-28 09:16:13.266683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f0d0800ada2a'
down_revision: Union[str, None] = 'cf7fba3cd1dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "transcript_id",
            sa.BigInteger,
            sa.ForeignKey("minutes.transcripts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema="minutes",
    )
    op.create_index(
        "idx_messages_transcript_created",
        "messages",
        ["transcript_id", "created_at"],
        schema="minutes",
    )


def downgrade() -> None:
    op.drop_index("idx_messages_transcript_created",
                  table_name="messages", schema="minutes")
    op.drop_table("messages", schema="minutes")