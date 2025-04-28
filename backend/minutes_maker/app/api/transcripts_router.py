from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..db import SessionLocal, models as M

router = APIRouter(prefix="/api", tags=["transcripts"])


def get_db() -> Session:               # unchanged
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- LIST & DETAIL ---------------------------------------------------
@router.get("/transcripts")
def list_transcripts(
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            M.Transcript.id,
            M.Transcript.file_id,
            M.File.filename,
            M.Transcript.language,
            M.Transcript.created_at,
        )
        .join(M.File, M.File.file_id == M.Transcript.file_id)
        .order_by(M.Transcript.created_at.desc())
        .limit(limit)
        .offset(offset)
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


# ---------- NEW: DELETE -----------------------------------------------------
@router.delete("/transcripts/{tid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcript(tid: int, db: Session = Depends(get_db)):
    """
    Permanently delete a transcript (and its cascading minutes_versions /
    transcript_chunks thanks to ON DELETE CASCADE).
    """
    tr = db.get(M.Transcript, tid)
    if not tr:
        raise HTTPException(404, "Not found")
    db.delete(tr)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
