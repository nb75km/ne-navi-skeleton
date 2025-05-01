from datetime import datetime
from typing import List

from diff_match_patch import diff_match_patch
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from common.security import current_active_user
from common.models.user import User

from ..db import SessionLocal, models as M # 既存の DB セッション取得関数

router = APIRouter(prefix="/api", tags=["diff"])
dmp = diff_match_patch()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Segment(BaseModel):
    op: str               # "equal" | "insert" | "delete"
    text: str


class DiffOut(BaseModel):
    from_id: int
    to_id: int
    generated_at: datetime
    segments: List[Segment]


@router.get("/diff/{from_id}/{to_id}", response_model=DiffOut)
def diff_versions(
    from_id: int,
    to_id: int,
    cleanup_semantic: bool = Query(
        True, description="diff_cleanupSemantic を適用するか"),
    db: Session = Depends(get_db),
    user: User = Depends(current_active_user),
):
    """
    2 つの MinutesVersion (Markdown) を比較し、
    diff-match-patch のセグメント配列を JSON で返す。
    """
    v1 = db.get(M.MinutesVersion, from_id)
    v2 = db.get(M.MinutesVersion, to_id)
    if (
        v1 is None
        or v2 is None
        or v1.user_id != user.id
        or v2.user_id != user.id
    ):
        raise HTTPException(404, "Version not found")

    diffs = dmp.diff_main(v1.markdown, v2.markdown)
    if cleanup_semantic:
        dmp.diff_cleanupSemantic(diffs)

    op_map = {-1: "delete", 0: "equal", 1: "insert"}
    segments = [{"op": op_map[o], "text": t} for o, t in diffs]

    return {
        "from_id": from_id,
        "to_id": to_id,
        "generated_at": datetime.utcnow(),
        "segments": segments,
    }
