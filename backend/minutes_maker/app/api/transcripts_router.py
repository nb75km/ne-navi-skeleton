from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from weasyprint import HTML
from docx import Document
from io import BytesIO
import markdown as md

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
@router.get("/minutes/{version_id}/export")
def export_minutes(version_id: int, format: str):
    """
    Export minutes_version markdown as md/docx/pdf.
    format: 'md' | 'docx' | 'pdf'
    """
    sess = SessionLocal()
    mv = sess.query(M.MinutesVersion).filter_by(id=version_id).first()
    if not mv:
        raise HTTPException(404, "Minutes version not found")
    source_md = mv.markdown

    if format == "md":
        return Response(source_md, media_type="text/markdown",
                        headers={"Content-Disposition": f"attachment; filename=minutes_{version_id}.md"})

    if format == "html":
        html = md.markdown(source_md)
        return Response(html, media_type="text/html",
                        headers={"Content-Disposition": f"attachment; filename=minutes_{version_id}.html"})

    if format == "pdf":
        html = md.markdown(source_md)
        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        pdf_io.seek(0)
        return StreamingResponse(pdf_io, media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename=minutes_{version_id}.pdf"})

    if format == "docx":
        doc = Document()
        for line in source_md.split("\n"):
            # 単純追加。必要に応じて見出し等を判定してスタイルを適用
            doc.add_paragraph(line)
        doc_io = BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        return StreamingResponse(doc_io,
                                 media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                 headers={"Content-Disposition": f"attachment; filename=minutes_{version_id}.docx"})

    raise HTTPException(400, "Unsupported format")

# --- 既存: DELETE ---
@router.delete("/transcripts/{tid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcript(tid: int, db: Session = Depends(get_db)):
    tr = db.get(M.Transcript, tid)
    if not tr:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(tr)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
