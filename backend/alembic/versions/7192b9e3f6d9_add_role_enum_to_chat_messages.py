"""add role enum to chat.messages

Revision ID: 7192b9e3f6d9
Revises: f0d0800ada2a
Create Date: 2025-04-29 12:34:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7192b9e3f6d9"
down_revision: Union[str, None] = "f0d0800ada2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) 既存 role 値の正規化（小文字化 & 不正値→'user'）
    conn.execute(sa.text("UPDATE chat.messages SET role = lower(role);"))
    conn.execute(
        sa.text(
            "UPDATE chat.messages "
            "SET role = 'user' "
            "WHERE role NOT IN ('user','assistant','system','agent');"
        )
    )

    # 2) Enum 型定義を作成して列を変換
    role_enum = sa.Enum("user", "assistant", "system", "agent", name="role")
    role_enum.create(conn, checkfirst=True)

    op.alter_column(
        "messages",
        "role",
        schema="chat",
        type_=role_enum,
        existing_type=sa.Text(),
        postgresql_using="role::role",
        nullable=False,
    )


def downgrade() -> None:
    role_enum = sa.Enum("user", "assistant", "system", "agent", name="role")
    op.alter_column(
        "messages",
        "role",
        schema="chat",
        type_=sa.Text(),
        existing_type=role_enum,
        postgresql_using="role::text",
        nullable=False,
    )
    role_enum.drop(op.get_bind(), checkfirst=True)
