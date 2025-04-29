from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import SessionLocal, models as M
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.llm import complete_with_minutes  # ← GPT-4o ラッパ

router = APIRouter(prefix="/api", tags=["minutes_chat"])

def get_db() -> Session:  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("minutes_chat/{transcript_id}", response_model=ChatResponse)
def chat_edit_minutes(
    transcript_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    ユーザー指示を受け取り、AI に議事録を編集してもらう。
    - 現在の最新版 MinutesVersion を取得
    - LLM に指示を送り、assistant の返答と (必要に応じ) 更新後 Markdown を得る
    - Markdown が変わった場合は新しい MinutesVersion を追加
    """
    latest: MinutesVersion | None = (
        db.query(MinutesVersion)
        .filter(MinutesVersion.transcript_id == transcript_id)
        .order_by(MinutesVersion.revision.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail="Minutes not found")

    assistant_msg, updated_md = complete_with_minutes(
        user_messages=payload.messages,
        user_input=payload.user_input,
        current_minutes=latest.markdown,
    )

    target = latest
    if updated_md.strip() != latest.markdown.strip():
        target = MinutesVersion(
            transcript_id=transcript_id,
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
