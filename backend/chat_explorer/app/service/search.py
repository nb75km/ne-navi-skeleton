from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector
from backend.chat_explorer.app.db import SessionLocal, models as M

def fulltext_query(sess: Session, text: str, limit: int = 50):
    pattern = f"%{text}%"
    return (
        sess.query(M.Message)
        .filter(M.Message.body.ilike(pattern))
        .order_by(M.Message.created_at.desc())
        .limit(limit)
        .all()
    )

def semantic_query(sess: Session, embedding: list[float], limit: int = 50):
    # <=> は pgvector のコサイン距離
    return (
        sess.query(M.Message)
        .order_by(M.Message.embedding.l2_distance(sa.cast(embedding, Vector)))
        .limit(limit)
        .all()
    )
