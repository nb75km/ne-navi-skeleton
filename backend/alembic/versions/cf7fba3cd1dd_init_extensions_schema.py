from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR

revision = "cf7fba3cd1dd"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # --- 拡張 ---
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # --- Japanese textsearch config ---
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_ts_config WHERE cfgname = 'japanese'
          ) THEN
            CREATE TEXT SEARCH CONFIGURATION japanese (COPY = simple);
          END IF;
        END;
        $$;
        """
    )

    # --- スキーマ ---
    op.execute("CREATE SCHEMA IF NOT EXISTS chat")
    op.execute("CREATE SCHEMA IF NOT EXISTS minutes")

    # --- messages (A1) ---
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("conversation_id", sa.Text, nullable=False),
        sa.Column("user_id", sa.Text),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema="chat",
    )
    op.execute(
        """
        CREATE INDEX messages_embedding_hnsw
        ON chat.messages
        USING hnsw (embedding vector_l2_ops)
        WITH (m = 16, ef_construction = 80)
        """
    )

    # --- transcripts (A2) ---
    op.create_table(
        "transcripts",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("file_id", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("ts", TSVECTOR,
                  sa.Computed("to_tsvector('japanese', content)",
                              persisted=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema="minutes",
    )
    op.execute(
        "CREATE INDEX transcripts_ts_idx ON minutes.transcripts USING GIN (ts)"
    )

def downgrade():
    op.drop_table("transcripts", schema="minutes")
    op.drop_table("messages", schema="chat")
    op.execute("DROP SCHEMA IF EXISTS minutes CASCADE")
    op.execute("DROP SCHEMA IF EXISTS chat CASCADE")