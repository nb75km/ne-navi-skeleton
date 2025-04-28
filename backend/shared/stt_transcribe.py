"""
OpenAI Whisper で音声ファイルを文字起こしし、
DB (transcripts / transcript_chunks) に保存する Celery タスク
"""
from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Optional

import boto3
import openai
from sqlalchemy.orm import Session

from shared.celery_app import celery_app
from minutes_maker.app import SessionLocal
from minutes_maker.app.db import models as M

openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# MinIO (S3-compatible) settings
# ---------------------------------------------------------------------------
_MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
_MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
_MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
_BUCKET = os.getenv("MINIO_BUCKET", "minutes-audio")

s3 = boto3.client(
    "s3",
    endpoint_url=_MINIO_ENDPOINT,
    aws_access_key_id=_MINIO_ACCESS_KEY,
    aws_secret_access_key=_MINIO_SECRET_KEY,
    region_name="us-east-1",
)

UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # ensure exists

# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------
@celery_app.task(name="minutes.stt.transcribe")
def transcribe_file(file_id: str) -> str:
    """
    1. /data/uploads or MinIO から音声を取得
    2. Whisper (verbose_json + segment) で文字起こし
    3. transcripts / transcript_chunks に保存
    """
    # ---- fetch object ------------------------------------------------------
    audio_bytes: Optional[bytes] = None
    filename: Optional[str] = None

    # ① ローカル /data/uploads
    local = next(UPLOAD_DIR.glob(f"{file_id}_*"), None)
    if local and local.is_file():
        audio_bytes = local.read_bytes()
        filename = local.name.split("_", 1)[1]

    # ② MinIO
    if audio_bytes is None:
        objs = s3.list_objects_v2(Bucket=_BUCKET, Prefix=f"{file_id}/")
        if "Contents" not in objs:
            raise FileNotFoundError(file_id)

        key = objs["Contents"][0]["Key"]
        buf = BytesIO()
        s3.download_fileobj(_BUCKET, key, buf)
        audio_bytes = buf.getvalue()
        filename = key.split("/")[-1]

    # ---- Whisper -----------------------------------------------------------
    whisper_rsp = openai.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes, "application/octet-stream"),
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )

    # TranscriptionVerbose オブジェクトは属性アクセス
    full_text: str = whisper_rsp.text.strip()
    language: str | None = getattr(whisper_rsp, "language", None)

    # ---- Persist to DB -----------------------------------------------------
    sess: Session = SessionLocal()
    try:
        tr = M.Transcript(file_id=file_id, language=language, content=full_text)
        sess.add(tr)
        sess.flush()

        for seg in whisper_rsp.segments:
            sess.add(
                M.TranscriptChunk(
                    transcript_id=tr.id,
                    start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000),
                    text=seg.text.strip(),
                )
            )

        sess.commit()
        return "ok"
    finally:
        sess.close()
