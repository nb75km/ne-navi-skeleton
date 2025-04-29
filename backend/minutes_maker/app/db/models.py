"""SQLAlchemy ORM models for the *Minutes Maker* (schema = "minutes")."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import enum
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Computed
from sqlalchemy.dialects import postgresql


class Base(DeclarativeBase):
    """Declarative base class bound to the *minutes* schema."""


# --------------------------------------------------------------------------- #
#  共通
# --------------------------------------------------------------------------- #
Base.metadata.schema = "minutes"  # type: ignore[attr-defined]


class JobStatus(str, enum.Enum):
    """DB / API で共通利用するジョブ状態 (大文字固定 ― マイグレーションと一致)"""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DRAFT_READY = "DRAFT_READY"
    FAILED = "FAILED"


# --------------------------------------------------------------------------- #
#  files
# --------------------------------------------------------------------------- #
class File(Base):
    __tablename__ = "files"

    file_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[Optional[str]]
    duration_sec: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    uploaded_by: Mapped[Optional[str]]
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    transcripts: Mapped[List["Transcript"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_files_uploaded_at", "uploaded_at"),)


# --------------------------------------------------------------------------- #
#  transcripts
# --------------------------------------------------------------------------- #
class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    file_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("minutes.files.file_id", ondelete="CASCADE"),
        nullable=False,
    )
    language: Mapped[Optional[str]] = mapped_column(String(8))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    verbose_json: Mapped[Optional[str]] = mapped_column(postgresql.JSON)
    ts: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('japanese', content)", persisted=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    file: Mapped["File"] = relationship(back_populates="transcripts")
    chunks: Mapped[List["TranscriptChunk"]] = relationship(
        back_populates="transcript", cascade="all, delete-orphan"
    )
    versions: Mapped[List["MinutesVersion"]] = relationship(
        back_populates="transcript", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        back_populates="transcript", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("transcripts_ts_idx", "ts", postgresql_using="gin"),)


# --------------------------------------------------------------------------- #
#  transcript_chunks
# --------------------------------------------------------------------------- #
class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transcript_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("minutes.transcripts.id", ondelete="CASCADE")
    )
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))
    ts: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('japanese', text)", persisted=True),
    )

    transcript: Mapped["Transcript"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index(
            "transcript_chunks_embedding_ivfflat",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": "100"},
        ),
        Index("transcript_chunks_ts_idx", "ts", postgresql_using="gin"),
    )


# --------------------------------------------------------------------------- #
#  minutes_versions
# --------------------------------------------------------------------------- #
class MinutesVersion(Base):
    __tablename__ = "minutes_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transcript_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("minutes.transcripts.id", ondelete="CASCADE")
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    transcript: Mapped["Transcript"] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint(
            "transcript_id", "version_no", name="uix_minutes_versions_no"
        ),
    )


# --------------------------------------------------------------------------- #
#  chat messages
# --------------------------------------------------------------------------- #
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transcript_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("minutes.transcripts.id", ondelete="CASCADE"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    transcript: Mapped[Optional["Transcript"]] = relationship(
        back_populates="messages"
    )


# --------------------------------------------------------------------------- #
#  jobs
# --------------------------------------------------------------------------- #
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    task_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    transcript_id: Mapped[Optional[int]]

    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="job_status", native_enum=False),
        default=JobStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow
    )


__all__ = [
    "Base",
    "File",
    "Transcript",
    "TranscriptChunk",
    "MinutesVersion",
    "Message",
    "Job",
    "JobStatus",
]
