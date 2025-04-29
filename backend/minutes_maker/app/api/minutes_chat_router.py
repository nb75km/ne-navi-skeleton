from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..db.models import MinutesVersion  # 正しい ORM を import&#8203;:contentReference[oaicite:4]{index=4}
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.llm import complete_with_minutes

router = APIRouter(prefix="/api", tags=["minutes_chat"])


def get_db() -> Session:  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/minutes_chat/{transcript_id}", response_model=ChatResponse)  # ← 先頭スラッシュ必須&#8203;:contentReference[oaicite:5]{index=5}
def chat_edit_minutes(
    transcript_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
):
    latest: MinutesVersion | None = (
        db.query(MinutesVersion)
        .filter(MinutesVersion.transcript_id == transcript_id)
        .order_by(MinutesVersion.version_no.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minutes not found")

    assistant_msg, updated_md = complete_with_minutes(
        user_messages=payload.messages,
        user_input=payload.user_input,
        current_minutes=latest.markdown,
    )

    target = latest
    if updated_md.strip() != latest.markdown.strip():
        target = MinutesVersion(
            transcript_id=transcript_id,
            version_no=latest.version_no + 1,
            markdown=updated_md,
            created_by=payload.user_id or "ui_user",
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    return ChatResponse(
        assistant_message=assistant_msg,
        version_id=target.id,
        markdown=target.markdown,
    )
