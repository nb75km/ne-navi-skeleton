import io
from .db import SessionLocal
from .db.models import Transcript
from docx import Document
import markdown as md
from weasyprint import HTML

def get_transcript(tid: int) -> Transcript | None:
    """同期的に Transcript レコードを取得"""
    with SessionLocal() as session:
        return session.get(Transcript, tid)

def export_file(tid: int, fmt: str) -> tuple[bytes, str]:
    """
    指定フォーマットでファイルを生成して (バイト列, mime_type) を返す。
    fmt: 'markdown'|'docx'|'pdf'|'html'
    """
    transcript = get_transcript(tid)
    if not transcript:
        raise ValueError("Transcript not found")

    # ここではトランスクリプトの content を Markdown テキストとして扱う
    text = transcript.content

    if fmt == "markdown":
        return text.encode("utf-8"), "text/markdown; charset=utf-8"

    elif fmt == "docx":
        doc = Document()
        for line in text.splitlines():
            doc.add_paragraph(line)
        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue(), (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )

    elif fmt == "pdf":
        # Markdown → HTML → PDF
        html = md.markdown(text)
        pdf = HTML(string=html).write_pdf()
        return pdf, "application/pdf"

    elif fmt == "html":
        html = md.markdown(text)
        return html.encode("utf-8"), "text/html; charset=utf-8"

    else:
        raise ValueError(f"Unsupported format: {fmt}")
