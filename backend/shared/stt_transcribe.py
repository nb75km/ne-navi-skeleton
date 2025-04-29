"""
OpenAI Whisper – oversized audio (25 MB+) 対応版
1. /data/uploads or MinIO からバイナリ取得
2. 16 kHz mono 32 kbps MP3 に再エンコード
3. 24 MB 単位にチャンク化 → Whisper API (verbose_json + segment/word)
4. タイムスタンプ補正後に transcripts / transcript_chunks へ保存
5. 保存完了後 draft_minutes.generate をキック
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

import boto3
import openai
from sqlalchemy.orm import Session

from shared.celery_app import celery_app
from minutes_maker.app import SessionLocal
from minutes_maker.app.db import models as M
from shared.draft_minutes import generate_minutes_draft

openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# Consts
# ---------------------------------------------------------------------------
MAX_BYTES = 24 * 1024 * 1024  # 24 MB (25 MB 制限より余裕)
BITRATE = "32k"  # 32 kbps CBR
SAMPLE_RATE = 16000  # 16 kHz mono
UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

def _run(cmd: List[str]):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())

# ---------------------------------------------------------------------------
# Re-encode & Split helpers
# ---------------------------------------------------------------------------

def reencode(src: Path) -> Path:
    out = src.with_suffix(".mp3")
    _run([
        "ffmpeg", "-y", "-i", str(src),
        "-ac", "1", "-ar", str(SAMPLE_RATE), "-b:a", BITRATE,
        str(out),
    ])
    return out


def probe_duration(path: Path) -> float:
    pp = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        stdout=subprocess.PIPE,
        check=True,
    )
    return float(pp.stdout)


def split_by_bytes(path: Path) -> List[Tuple[Path, float]]:
    duration = probe_duration(path)
    bps = int(BITRATE.replace("k", "")) * 1024 // 8
    approx_sec = MAX_BYTES / bps * 0.9

    chunks: List[Tuple[Path, float]] = []
    offset = 0.0
    idx = 0
    while offset < duration:
        dur = min(approx_sec, duration - offset)
        out = path.parent / f"seg_{idx:04d}.mp3"
        _run(["ffmpeg", "-y", "-i", str(path), "-ss", str(offset), "-t", str(dur), "-c", "copy", str(out)])
        if out.stat().st_size > MAX_BYTES:
            # fallback: half duration
            dur /= 2
            _run(["ffmpeg", "-y", "-i", str(path), "-ss", str(offset), "-t", str(dur), "-c", "copy", str(out)])
        chunks.append((out, offset))
        offset += dur
        idx += 1
    return chunks

# ---------------------------------------------------------------------------
# Celery Task
# ---------------------------------------------------------------------------

@celery_app.task(name="minutes.stt.transcribe")
def transcribe_audio(file_id: str) -> str:
    """Main entry – size-aware transcription with timestamp merge."""

    # -------------------------------------------------- 1. fetch audio bytes
    audio_path: Optional[Path] = None
    local = next(UPLOAD_DIR.glob(f"{file_id}_*"), None)
    if local and local.is_file():
        audio_path = local
    else:
        objs = s3.list_objects_v2(Bucket=_BUCKET, Prefix=f"{file_id}/")
        if "Contents" not in objs:
            raise FileNotFoundError(file_id)
        key = objs["Contents"][0]["Key"]
        tmpdir = tempfile.mkdtemp()
        tmp_path = Path(tmpdir) / key.split("/")[-1]
        with open(tmp_path, "wb") as fp:
            s3.download_fileobj(_BUCKET, key, fp)
        audio_path = tmp_path

    # -------------------------------------------------- 2. re-encode + split
    encoded = reencode(audio_path)
    segments = [(encoded, 0.0)] if encoded.stat().st_size <= MAX_BYTES else split_by_bytes(encoded)

    full_text_parts: List[str] = []
    all_segments: List[dict] = []

    # -------------------------------------------------- 3. Whisper each chunk
    for seg_path, offset in segments:
        with open(seg_path, "rb") as fp:
            rsp = openai.audio.transcriptions.create(
                model="whisper-1",
                file=fp,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"],
            )

        # -------- SDK v1.x (BaseModel) / v0.x (str JSON) 両対応 ----------
        try:
            data = rsp.model_dump()  # Pydantic v2 BaseModel → dict
        except AttributeError:
            data = json.loads(rsp)   # 旧 SDK → str
        # ---------------------------------------------------------------

        for s in data["segments"]:
            s["start"] += offset
            s["end"] += offset
        for w in data.get("words", []):
            w["start"] += offset
            w["end"] += offset
        all_segments.extend(data["segments"])
        full_text_parts.append(data["text"].strip())

    full_text = "\n".join(full_text_parts)
    all_segments.sort(key=lambda s: s["start"])

    # -------------------------------------------------- 4. save to DB
    sess: Session = SessionLocal()
    try:
        tr = M.Transcript(file_id=file_id, content=full_text, verbose_json=json.dumps({"segments": all_segments}))
        sess.add(tr)
        sess.flush()  # get tr.id
        for seg in all_segments:
            sess.add(
                M.TranscriptChunk(
                    transcript_id=tr.id,
                    start_ms=int(seg["start"] * 1000),
                    end_ms=int(seg["end"] * 1000),
                    text=seg["text"].strip(),
                )
            )
        sess.commit()
        transcript_id = tr.id
    finally:
        sess.close()

    # -------------------------------------------------- 5. kick draft minutes
    generate_minutes_draft.delay(transcript_id)
    return "ok"

# backward-compat alias
transcribe_file = transcribe_audio
