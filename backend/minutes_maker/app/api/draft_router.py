from fastapi import APIRouter, HTTPException, Depends
from common.security import current_active_user
from common.models.user import User
from sqlalchemy.orm import Session
from ..db import SessionLocal, models as M

from pydantic import BaseModel

from shared.draft_minutes import generate_minutes_draft

router = APIRouter(prefix="/api", tags=["minutes-draft"])


class DraftIn(BaseModel):
    model: str = "gpt-4o-mini"  # 選択モデル


@router.post("/{transcript_id}/draft")
async def create_draft(
        transcript_id: int,
        body: DraftIn,
        user: User = Depends(current_active_user),
        db: Session = Depends(lambda: SessionLocal()),
):
    tr = db.get(M.Transcript, transcript_id)
    if tr is None or tr.user_id != user.id:
        raise HTTPException(404, "Transcript not found")
    """Trigger GPT-based minutes draft generation."""
    try:
        task = generate_minutes_draft.delay(transcript_id, body.model, str(user.id))
        return {"task_id": task.id, "queued": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
