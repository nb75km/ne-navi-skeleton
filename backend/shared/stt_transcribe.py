"""
OpenAI Whisper – oversized audio (25 MB+) 対応版
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import boto3
import openai
from celery import shared_task
from sqlalchemy.orm import Session

from shared.celery_app import celery_app
from minutes_maker.app import SessionLocal
from minutes_maker.app.db import models as M
from shared.draft_minutes import generate_minutes_draft

openai.api_key = os.getenv("OPENAI_API_KEY")

# --------------------------------------------------------------------------- #
#  Consts
# --------------------------------------------------------------------------- #
MAX_BYTES = 24 * 1024 * 1024
BITRATE = "32k"
SAMPLE_RATE = 16000
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


# --------------------------------------------------------------------------- #
#  Re-encode & split
# --------------------------------------------------------------------------- #
def reencode(src: Path) -> Path:
    """
    Always create **new** file.
    src=xxx.mp3 -> xxx.reenc.mp3
    """
    if src.suffix.lower() == ".mp3":
        out = src.with_suffix(".reenc.mp3")
    else:
        out = src.with_suffix(".mp3")

    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-b:a",
            BITRATE,
            str(out),
        ]
    )
    return out


def probe_duration(path: Path) -> float:
    pp = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
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
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-ss",
                str(offset),
                "-t",
                str(dur),
                "-c",
                "copy",
                str(out),
            ]
        )
        if out.stat().st_size > MAX_BYTES:  # safety fallback
            dur /= 2
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(path),
                    "-ss",
                    str(offset),
                    "-t",
                    str(dur),
                    "-c",
                    "copy",
                    str(out),
                ]
            )
        chunks.append((out, offset))
        offset += dur
        idx += 1
    return chunks


# --------------------------------------------------------------------------- #
#  Celery task
# --------------------------------------------------------------------------- #
@celery_app.task(name="minutes.transcribe_and_generate")
def transcribe_and_generate_minutes(audio_file_id: str, job_id: str):
    """STT → minutes draft までを一括で処理し、途中経過を jobs テーブル更新"""

    # ---------- Job row: set PROCESSING ----------
    sess: Session = SessionLocal()
    job = sess.get(M.Job, job_id)
    if not job:  # safety
        sess.close()
        return
    job.status = M.JobStatus.PROCESSING
    sess.commit()
    sess.close()

    try:
        # 1) 音声取得
        local_path: Optional[Path] = next(
            UPLOAD_DIR.glob(f"{audio_file_id}_*"), None
        )
        if not local_path:
            raise FileNotFoundError(audio_file_id)

        # 2) re-encode + split
        encoded = reencode(local_path)
        segments = (
            [(encoded, 0.0)]
            if encoded.stat().st_size <= MAX_BYTES
            else split_by_bytes(encoded)
        )

        # 3) Whisper
        full_text_parts: List[str] = []
        all_segments: List[dict] = []
        for seg_path, offset in segments:
            with open(seg_path, "rb") as fp:
                rsp = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=fp,
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"],
                )
            data = rsp.model_dump() if hasattr(rsp, "model_dump") else json.loads(rsp)

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

        # 4) DB へ保存
        sess = SessionLocal()
        tr = M.Transcript(
            file_id=audio_file_id,
            content=full_text,
            verbose_json=json.dumps({"segments": all_segments}),
        )
        sess.add(tr)
        sess.flush()
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
        sess.close()

        # 5) Draft minutes
        generate_minutes_draft.delay(transcript_id)

        # ---------- Job row: set DRAFT_READY ----------
        sess = SessionLocal()
        job = sess.get(M.Job, job_id)
        if job:
            job.transcript_id = transcript_id
            job.status = M.JobStatus.DRAFT_READY
            sess.commit()
        sess.close()

    except Exception:
        sess = SessionLocal()
        job = sess.get(M.Job, job_id)
        if job:
            job.status = M.JobStatus.FAILED
            sess.commit()
        sess.close()
        raise
