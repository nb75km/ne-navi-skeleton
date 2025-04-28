from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.draft_minutes import generate_minutes_draft

router = APIRouter(prefix="/api", tags=["minutes-draft"])


class DraftIn(BaseModel):
    model: str = "gpt-4o-mini"  # 選択モデル


@router.post("/{transcript_id}/draft")
async def create_draft(transcript_id: int, body: DraftIn):
    """Trigger GPT-based minutes draft generation."""
    try:
        task = generate_minutes_draft.delay(transcript_id, body.model)
        return {"task_id": task.id, "queued": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
