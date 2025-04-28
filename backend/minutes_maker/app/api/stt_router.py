"""
/stt  –  Whisper 音声文字起こしエンドポイント
--------------------------------------------
POST multipart/form-data
  • audio=<file>    : mp3 / wav / m4a / mp4 など
  • lang=<ISO code> : ja / en / id … （省略可。自動判定）

返却 JSON
{
  "file_id":        "<uuid>",
  "transcript_id":  <int>,
  "content":        "<文字起こし結果>",
  "language":       "<ISO code | null>"
}
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from openai import OpenAI, OpenAIError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from ..db import SessionLocal, models as M

router = APIRouter(prefix="/stt", tags=["stt"])
oai = OpenAI()  # env var OPENAI_API_KEY


# --------------------------------------------------------------------------- #
# DB dependency
# --------------------------------------------------------------------------- #
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Pydantic schema
# --------------------------------------------------------------------------- #
class TranscriptOut(BaseModel):
    file_id: str
    transcript_id: int
    content: str
    language: str | None = None

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------- #
# Whisper helper (with retry)
# --------------------------------------------------------------------------- #
@retry(wait=wait_exponential_jitter(1, 20), stop=stop_after_attempt(4))
def _transcribe(
    filename: str,
    content: bytes,
    mime: str,
    language: str | None = None,
) -> str:
    try:
        rsp = oai.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, content, mime),
            response_format="text",
            language=language,
        )
        return rsp  # type: ignore[return-value]
    except OpenAIError as e:
        raise RuntimeError(str(e)) from e


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #
@router.post(
    "",  # accepts both /stt and /stt/
    response_model=TranscriptOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_transcript(
    audio: UploadFile = File(...),
    lang: str | None = Form(
        None,
        description="ISO-639 言語コード。省略時は Whisper 自動判定",
    ),
    db: Session = Depends(get_db),
):
    # --- basic type check ----------------------------------------------------
    ctype = (audio.content_type or "").lower()
    filename_lc = (audio.filename or "").lower()
    allowed_ext = (".mp3", ".wav", ".m4a", ".mp4")

    is_audio_mime = ctype.startswith("audio/")
    is_octet_with_audio_ext = (
        ctype == "application/octet-stream" and filename_lc.endswith(allowed_ext)
    )
    if not (is_audio_mime or ctype == "video/mp4" or is_octet_with_audio_ext):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported media type: {ctype or 'unknown'}",
        )

    # --- read bytes & call Whisper ------------------------------------------
    data = await audio.read()
    try:
        text: str = _transcribe(audio.filename, data, audio.content_type, language=lang)
    except RuntimeError as e:
        raise HTTPException(502, f"Whisper API error: {e}") from e

    # --- persist to DB -------------------------------------------------------
    file_id = str(uuid4())

    file_row = M.File(
        file_id=file_id,
        filename=audio.filename,
        mime_type=audio.content_type,
    )
    db.add(file_row)

    trans_row = M.Transcript(
        file_id=file_id,
        language=lang,
        content=text,
    )
    db.add(trans_row)
    db.commit()
    db.refresh(trans_row)

    # --- response ------------------------------------------------------------
    return TranscriptOut(
        file_id=file_id,
        transcript_id=trans_row.id,
        content=text,
        language=lang,
    )
