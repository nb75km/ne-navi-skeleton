from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal, models as M
from ..service import export_file

router = APIRouter(prefix="/api", tags=["transcripts"])

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 既存: LIST ---
@router.get("/transcripts", status_code=status.HTTP_200_OK)
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

# --- 既存: DETAIL ---
@router.get("/transcripts/{tid}", status_code=status.HTTP_200_OK)
def get_transcript(tid: int, db: Session = Depends(get_db)):
    t = (
        db.query(M.Transcript, M.File.filename)
        .join(M.File, M.File.file_id == M.Transcript.file_id)
        .filter(M.Transcript.id == tid)
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    tr, fname = t
    return {
        "id": tr.id,
        "file_id": tr.file_id,
        "filename": fname,
        "language": tr.language,
        "created_at": tr.created_at,
        "content": tr.content,
    }

# --- 新規: EXPORT ---
@router.get("/transcripts/{tid}/export", status_code=status.HTTP_200_OK)
def export_transcript(
    tid: int,
    format: str = Query(..., description="export format: markdown|docx|pdf|html"),
    db: Session = Depends(get_db),
):
    allowed = {"markdown", "docx", "pdf", "html"}
    if format not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported format")

    try:
        content, mime = export_file(tid, format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

    ext = "md" if format == "markdown" else format
    filename = f"transcript_{tid}.{ext}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([content]), media_type=mime, headers=headers)

# --- 既存: DELETE ---
@router.delete("/transcripts/{tid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcript(tid: int, db: Session = Depends(get_db)):
    tr = db.get(M.Transcript, tid)
    if not tr:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(tr)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
