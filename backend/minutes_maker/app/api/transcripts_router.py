from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import SessionLocal, models as M

router = APIRouter(prefix="/api", tags=["transcripts"])

def get_db() -> Session:
    db = SessionLocal();  yield db;  db.close()

@router.get("/transcripts")
def list_transcripts(
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = (
        db.query(M.Transcript.id,
                 M.Transcript.file_id,
                 M.File.filename,
                 M.Transcript.language,
                 M.Transcript.created_at)
        .join(M.File, M.File.file_id == M.Transcript.file_id)
        .order_by(M.Transcript.created_at.desc())
        .limit(limit).offset(offset)
    )
    return {"items": [t._asdict() for t in q]}

@router.get("/transcripts/{tid}")
def get_transcript(tid: int, db: Session = Depends(get_db)):
    t = (
        db.query(M.Transcript, M.File.filename)
        .join(M.File, M.File.file_id == M.Transcript.file_id)
        .filter(M.Transcript.id == tid)
        .first()
    )
    if not t:
        raise HTTPException(404, "Not found")
    tr, fname = t
    return {
        "id": tr.id,
        "file_id": tr.file_id,
        "filename": fname,
        "language": tr.language,
        "created_at": tr.created_at,
        "content": tr.content,
    }
