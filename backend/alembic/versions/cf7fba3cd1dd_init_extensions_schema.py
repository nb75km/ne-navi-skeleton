from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB

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

    # --- conversations (A1) ---
    op.create_table(
        "conversations",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("conversation_uid", sa.Text, nullable=False),
        sa.Column("user_id", sa.Text),
        sa.Column("title", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("conversation_uid", name="uix_conversation_uid"),
        schema="chat",
    )
    op.create_index(
        "idx_conversations_user_created",
        "conversations",
        ["user_id", "created_at"],
        schema="chat"
    )

    # --- messages (A1) ---
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("conversation_id", sa.BigInteger,
                  sa.ForeignKey("chat.conversations.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema="chat",
    )
    op.create_index(
        "messages_conv_created_desc",
        "messages",
        ["conversation_id", "created_at"],
        schema="chat"
    )
    op.execute(
        """
        CREATE INDEX messages_embedding_hnsw
        ON chat.messages
        USING hnsw (embedding vector_l2_ops)
        WITH (m = 16, ef_construction = 80)
        """
    )

    # --- message_tags (A1) ---
    op.create_table(
        "message_tags",
        sa.Column("message_id", sa.BigInteger,
                  sa.ForeignKey("chat.messages.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("tag", sa.String(32), primary_key=True),
        schema="chat",
    )

    # --- agent_jobs (A1) ---
    op.create_table(
        "agent_jobs",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("message_id", sa.BigInteger,
                  sa.ForeignKey("chat.messages.id", ondelete="CASCADE")),
        sa.Column("agent_name", sa.Text, nullable=False),
        sa.Column("status", sa.Text, server_default="pending"),
        sa.Column("result_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        schema="chat",
    )
    op.create_index("idx_agent_jobs_status", "agent_jobs",
                    ["status"], schema="chat")

    # --- files (A2) ---
    op.create_table(
        "files",
        sa.Column("file_id", sa.Text, primary_key=True),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("mime_type", sa.Text),
        sa.Column("duration_sec", sa.Numeric(7, 2)),
        sa.Column("uploaded_by", sa.Text),
        sa.Column("uploaded_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        schema="minutes",
    )

    # --- transcripts (A2) ---
    op.create_table(
        "transcripts",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("file_id", sa.Text,
                  sa.ForeignKey("minutes.files.file_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("language", sa.String(8)),
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

    # --- transcript_chunks (A2) ---
    op.create_table(
        "transcript_chunks",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("transcript_id", sa.BigInteger,
                  sa.ForeignKey("minutes.transcripts.id", ondelete="CASCADE")),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("ts", TSVECTOR,
                  sa.Computed("to_tsvector('japanese', text)", persisted=True)),
        schema="minutes",
    )
    op.execute(
        """
        CREATE INDEX transcript_chunks_embedding_ivfflat
        ON minutes.transcript_chunks
        USING ivfflat (embedding vector_l2_ops)
        WITH (lists = 100)
        """
    )
    op.execute(
        "CREATE INDEX transcript_chunks_ts_idx ON minutes.transcript_chunks USING GIN (ts)"
    )

    # --- minutes_versions (A2) ---
    op.create_table(
        "minutes_versions",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("transcript_id", sa.BigInteger,
                  sa.ForeignKey("minutes.transcripts.id", ondelete="CASCADE")),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("markdown", sa.Text, nullable=False),
        sa.Column("created_by", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("transcript_id", "version_no",
                            name="uix_minutes_versions_no"),
        schema="minutes",
    )

def downgrade():
    op.drop_table("minutes_versions", schema="minutes")
    op.drop_table("transcript_chunks", schema="minutes")
    op.drop_table("files", schema="minutes")
    op.drop_table("agent_jobs", schema="chat")
    op.drop_table("message_tags", schema="chat")
    op.drop_table("messages", schema="chat")
    op.drop_index("idx_conversations_user_created", table_name="conversations", schema="chat")
    op.drop_table("conversations", schema="chat")
    op.drop_table("transcripts", schema="minutes")
    op.execute("DROP SCHEMA IF EXISTS minutes CASCADE")
    op.execute("DROP SCHEMA IF EXISTS chat CASCADE")