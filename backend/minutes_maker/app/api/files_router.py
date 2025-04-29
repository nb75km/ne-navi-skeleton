"""音声ファイルのアップロード API。

1. /data/uploads へ保存
2. files テーブルにレコード作成
3. jobs テーブルにレコード作成（Celery task_id をそのまま主キーに）
4. Celery へ STT + 議事録ドラフト生成タスクを投入
   - task 引数: (audio_file_id, job_id)
5. {file_id, job_id} を返す
"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from minutes_maker.app import SessionLocal
from minutes_maker.app.db import models as M
from shared.stt_transcribe import transcribe_and_generate_minutes

router = APIRouter(prefix="/api", tags=["files"])

UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def _save_file_to_disk(f: UploadFile, dst: Path):
    """UploadFile から bytes を読み込んで dst へ保存"""
    dst.write_bytes(f.file.read())


# --------------------------------------------------------------------------- #
#  endpoint
# --------------------------------------------------------------------------- #
@router.post("/files")
async def upload_file(file: UploadFile = File(...)):
    # ---------- 1. ファイル保存 ------------------------------------------------
    file_id = str(uuid4())
    dst = UPLOAD_DIR / f"{file_id}_{file.filename}"
    try:
        _save_file_to_disk(file, dst)
    except Exception as exc:
        raise HTTPException(500, f"disk save failed: {exc}") from exc

    # ---------- 2. DB insert: files ------------------------------------------
    sess: Session = SessionLocal()
    try:
        sess.add(
            M.File(
                file_id=file_id,
                filename=file.filename,
                mime_type=file.content_type,
                uploaded_by="ui_user",
            )
        )
        sess.commit()
    finally:
        sess.close()

    # ---------- 3. Celery task & jobs ----------------------------------------
    # Celery へ投入すると task_id が返る → これをそのまま jobs.id に採用
    task = transcribe_and_generate_minutes.delay(file_id, None)
    job_id = task.id

    sess = SessionLocal()
    try:
        sess.add(
            M.Job(
                id=job_id,          # ← primary key を task.id に固定
                task_id=task.id,
                status=M.JobStatus.PENDING,
            )
        )
        sess.commit()
    finally:
        sess.close()

    # ---------- 4. task 引数を確定させる --------------------------------------
    # 第一段階で None を渡していた job_id を、確定した値に上書きする
    # （Celery 5.4 の .replace() を利用）
    task.replace(args=(file_id, job_id))

    return {"file_id": file_id, "job_id": job_id}
