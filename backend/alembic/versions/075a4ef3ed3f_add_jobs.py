"""add jobs

Revision ID: 075a4ef3ed3f
Revises: 367d90de1bf0
Create Date: 2025-04-29 10:52:47.568928
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ★ 追加: Vector 型を使うため
import pgvector.sqlalchemy          # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "075a4ef3ed3f"
down_revision: Union[str, None] = "367d90de1bf0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- enum ---
    job_status = sa.Enum(
        "PENDING", "PROCESSING", "DRAFT_READY", "FAILED",
        name="job_status", native_enum=False
    )
    job_status.create(op.get_bind(), checkfirst=True)   # ← Enum だけ先に作る

    # --- jobs table ---
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("transcript_id", sa.Integer(), nullable=True),
        sa.Column("status", job_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        schema="minutes",
    )
    op.create_index(
        "ix_minutes_jobs_task_id",
        "jobs",
        ["task_id"],
        unique=True,
        schema="minutes",
    )


def downgrade() -> None:
    op.drop_index("ix_minutes_jobs_task_id", table_name="jobs", schema="minutes")
    op.drop_table("jobs", schema="minutes")
    sa.Enum(name="job_status").drop(op.get_bind(), checkfirst=True)

