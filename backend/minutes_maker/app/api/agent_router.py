from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
import json as _json

from ..db import SessionLocal, models as M

router = APIRouter(prefix="/api", tags=["agent"])
oai = OpenAI()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Ask(BaseModel):
    body: str
    # transcript_id を API へ含めるようにフロントでも送信してください
    transcript_id: int

class EditResponse(BaseModel):
    chatResponse: str
    editedMinutes: str
    versionNo: int

@router.post("/agent", response_model=EditResponse)
def call_agent(q: Ask, db: Session = Depends(get_db)):
    # 1) ユーザー発話を保存
    db.add(M.Message(transcript_id=q.transcript_id, role="user", body=q.body))
    db.commit()

    # 2) AI 呼び出し
    system_msg = (
        "You are a meeting minutes editor. "
        "The user prompt includes the full minutes. "
        "Respond in strict JSON with keys 'chatResponse' and 'editedMinutes'."
    )
    rsp = oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": q.body},
        ],
        temperature=0.4,
    )
    answer = rsp.choices[0].message.content

    # 3) JSON パース
    try:
        data = _json.loads(answer)
        chat_resp = data["chatResponse"]
        edited_raw = data["editedMinutes"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {e}")

    # 4) dict/list は文字列化して保存
    if isinstance(edited_raw, (dict, list)):
        edited_body = _json.dumps(edited_raw, ensure_ascii=False)
    else:
        edited_body = str(edited_raw)

    # 5) Assistant コメントを保存
    db.add(M.Message(transcript_id=q.transcript_id, role="assistant", body=chat_resp))
    db.commit()

    # 6) 編集後議事録を Message テーブルにも保存（履歴）
    db.add(M.Message(transcript_id=q.transcript_id, role="assistant", body=edited_body))
    db.commit()

    # 7) 最新 version_no を計算して MinutesVersion に保存
    last_mv = (
        db.query(M.MinutesVersion)
          .filter(M.MinutesVersion.transcript_id == q.transcript_id)
          .order_by(M.MinutesVersion.version_no.desc())
          .first()
    )
    next_ver = (last_mv.version_no if last_mv else 0) + 1
    mv = M.MinutesVersion(
        transcript_id=q.transcript_id,
        version_no=next_ver,
        markdown=edited_body,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    # 8) レスポンスを返却
    return {
        "chatResponse": chat_resp,
        "editedMinutes": edited_body,
        "versionNo": mv.version_no,
    }

