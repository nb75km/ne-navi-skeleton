from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..service import search as svc

router = APIRouter(tags=["search"])

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    body: str
    created_at: str

    # Pydantic v2
    model_config = ConfigDict(from_attributes=True)

@router.get("/search", response_model=list[MessageOut])
def search_messages(
    q: str = Query(..., description="検索文字列"),
    mode: str = Query("fulltext", enum=["fulltext", "semantic", "hybrid"]),
    top_k: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    if mode == "fulltext":
        return svc.fulltext_query(db, q, top_k)
    elif mode == "semantic":
        # NOTE: embedding 生成部は省略。ここではダミー0ベクトル
        return svc.semantic_query(db, [0.0] * 1536, top_k)
    else:  # hybrid
        ft = {m.id: m for m in svc.fulltext_query(db, q, top_k)}
        vec = svc.semantic_query(db, [0.0] * 1536, top_k)
        # 重複排除 + 順序単純結合
        result = list(ft.values()) + [m for m in vec if m.id not in ft][: top_k - len(ft)]
        return result
