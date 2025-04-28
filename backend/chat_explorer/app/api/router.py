from __future__ import annotations

from typing import Annotated, List, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.common.deps import db_session  # type: ignore
from . import schemas
from ..db import models as M
from .search_router import router as search_router

router = APIRouter(prefix="/api", tags=["chat_explorer"])
router.include_router(search_router)



def _paginate(
    stmt,
    sess: Session,
    schema_cls: Type[schemas.BaseModel],
    *,
    limit: int,
    offset: int,
):
    total = sess.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = sess.execute(stmt.limit(limit).offset(offset)).scalars().all()
    items = [schema_cls.model_validate(r, from_attributes=True) for r in rows]
    return schemas.Paginated(total=total, items=items)


@router.get("/conversations", response_model=schemas.Paginated)
def list_conversations(
    q: str | None = Query(None, description="Full-text search (ILIKE %q%)"),
    limit: int = Query(20, le=100),
    offset: int = 0,
    sess: Annotated[Session, Depends(db_session)] = None,  # type: ignore[assignment]
):
    stmt = select(M.Conversation).order_by(M.Conversation.created_at.desc())
    if q:
        stmt = stmt.where(M.Conversation.title.ilike(f"%{q}%"))
    return _paginate(stmt, sess, schemas.Conversation, limit=limit, offset=offset)


@router.get("/messages", response_model=schemas.Paginated)
def list_messages(
    conversation_id: int | None = None,
    search: str | None = Query(None, description="Full-text search inside body"),
    similar_to: int | None = Query(
        None,
        description="Return messages similar (vector) to given message ID",
    ),
    limit: int = Query(50, le=200),
    offset: int = 0,
    sess: Annotated[Session, Depends(db_session)] = None,  # type: ignore[assignment]
):
    stmt = select(M.Message)
    if conversation_id:
        stmt = stmt.where(M.Message.conversation_id == conversation_id)
    if search:
        stmt = stmt.where(M.Message.body.ilike(f"%{search}%"))
    if similar_to is not None:
        base_vec = sess.scalar(
            select(M.Message.embedding).where(M.Message.id == similar_to)
        )
        if base_vec is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="base message not found or missing embedding")
        stmt = (
            select(M.Message)
            .where(M.Message.embedding != None)  # noqa: E711
            .order_by(M.Message.embedding.l2_distance(base_vec))
        )
    stmt = stmt.order_by(M.Message.created_at.asc())
    return _paginate(stmt, sess, schemas.Message, limit=limit, offset=offset)
