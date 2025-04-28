# backend/chat_explorer/app/db/models.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass

Base.metadata.schema = "chat"

class Role(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_uid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[str | None]
    title: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat.conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[Role] = mapped_column(PgEnum(Role), nullable=False)
    body: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Vector] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    tags: Mapped[List["MessageTag"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    agent_jobs: Mapped[List["AgentJob"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("length(body) > 0", name="chk_message_body_nonempty"),
    )


class MessageTag(Base):
    __tablename__ = "message_tags"

    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat.messages.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(32), primary_key=True)

    message: Mapped[Message] = relationship(back_populates="tags")


class AgentJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class AgentJob(Base):
    __tablename__ = "agent_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat.messages.id", ondelete="CASCADE")
    )
    agent_name: Mapped[str]
    status: Mapped[AgentJobStatus] = mapped_column(
        PgEnum(AgentJobStatus), default=AgentJobStatus.PENDING
    )
    result_json: Mapped[str | None]  # JSONB を TEXT で簡易扱い
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    message: Mapped[Message] = relationship(back_populates="agent_jobs")