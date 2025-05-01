"""add users table + user_id FKs   ← 目的を明示

Revision ID: aa642dc3f33d
Revises: 075a4ef3ed3f
Create Date: 2025-05-01 03:04:55.157828
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ── revision identifiers ──────────────────────────────────────────────────────
revision: str | None = "aa642dc3f33d"
down_revision: str | None = "075a4ef3ed3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── upgrade ───────────────────────────────────────────────────────────────────
def upgrade() -> None:
    """Create public.users and add user_id FKs to minutes schema."""
    # 1) users テーブル（public スキーマ）
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        "ix_public_users_email",
        "users",
        ["email"],
        unique=True,
        schema="public",
    )

    # 2) minutes.files へ user_id 列
    op.add_column(
        "files",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="minutes",
    )
    op.create_index(
        "ix_minutes_files_user_id",
        "files",
        ["user_id"],
        schema="minutes",
    )
    op.create_foreign_key(
        None,
        "files",
        "users",
        ["user_id"],
        ["id"],
        source_schema="minutes",
        referent_schema="public",
        ondelete="SET NULL",
    )

    # 3) minutes.transcripts へ user_id 列
    op.add_column(
        "transcripts",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="minutes",
    )
    op.create_index(
        "ix_minutes_transcripts_user_id",
        "transcripts",
        ["user_id"],
        schema="minutes",
    )
    op.create_foreign_key(
        None,
        "transcripts",
        "users",
        ["user_id"],
        ["id"],
        source_schema="minutes",
        referent_schema="public",
        ondelete="SET NULL",
    )

    # 4) minutes.minutes_versions へ user_id 列
    op.add_column(
        "minutes_versions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="minutes",
    )
    op.create_index(
        "ix_minutes_minutes_versions_user_id",
        "minutes_versions",
        ["user_id"],
        schema="minutes",
    )
    op.create_foreign_key(
        None,
        "minutes_versions",
        "users",
        ["user_id"],
        ["id"],
        source_schema="minutes",
        referent_schema="public",
        ondelete="SET NULL",
    )


# ── downgrade ────────────────────────────────────────────────────────────────
def downgrade() -> None:
    """Remove user_id FKs and drop public.users."""
    # minutes.minutes_versions
    op.drop_constraint(None, "minutes_versions", schema="minutes", type_="foreignkey")
    op.drop_index("ix_minutes_minutes_versions_user_id", table_name="minutes_versions", schema="minutes")
    op.drop_column("minutes_versions", "user_id", schema="minutes")

    # minutes.transcripts
    op.drop_constraint(None, "transcripts", schema="minutes", type_="foreignkey")
    op.drop_index("ix_minutes_transcripts_user_id", table_name="transcripts", schema="minutes")
    op.drop_column("transcripts", "user_id", schema="minutes")

    # minutes.files
    op.drop_constraint(None, "files", schema="minutes", type_="foreignkey")
    op.drop_index("ix_minutes_files_user_id", table_name="files", schema="minutes")
    op.drop_column("files", "user_id", schema="minutes")

    # public.users
    op.drop_index("ix_public_users_email", table_name="users", schema="public")
    op.drop_table("users", schema="public")
