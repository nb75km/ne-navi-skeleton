# minutes_maker/app/api/agent_router.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
from ..db import SessionLocal, models as M

router = APIRouter(tags=["agent"])          # prefix は親 /api が付く

oai = OpenAI()                              # OPENAI_API_KEY が env にある前提

def get_db() -> Session:
    db = SessionLocal();  yield db;  db.close()

class Ask(BaseModel):
    body: str
    model: str = "gpt-4o-mini"

@router.post("/agent")
def call_agent(q: Ask, db: Session = Depends(get_db)):
    # --- ユーザメッセージ保存 --------------------------------------------------
    db.add(M.Message(transcript_id=None, role="user", body=q.body))
    db.commit()

    # --- OpenAI へ問い合わせ ---------------------------------------------------
    rsp = oai.chat.completions.create(
        model=q.model,
        messages=[
            {"role": "system", "content": "あなたは優秀な秘書です。"},
            {"role": "user", "content": q.body},
        ],
        temperature=0.4,
    )
    answer = rsp.choices[0].message.content

    # --- アシスタントの返答も保存 --------------------------------------------
    db.add(M.Message(transcript_id=None, role="assistant", body=answer))
    db.commit()

    return {"assistant": {"body": answer}}
