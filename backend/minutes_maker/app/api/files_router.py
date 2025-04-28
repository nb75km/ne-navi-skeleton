from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from ..db import models as M
from .. import SessionLocal
from shared.stt_transcribe import transcribe_file   # Celery task

router = APIRouter(prefix="/api", tags=["files"])


def _save_file_to_disk(f: UploadFile, dst: Path):
    dst.write_bytes(f.file.read())


@router.post("/files")
async def upload_file(file: UploadFile = File(...)):
    """
    1. /data/uploads に保存
    2. DB files テーブル登録
    3. Celery に STT タスク投入 → {file_id, task_id} を返す
    """
    file_id = str(uuid4())
    dst = Path("/data/uploads") / f"{file_id}_{file.filename}"
    try:
        _save_file_to_disk(file, dst)
    except Exception as exc:
        raise HTTPException(500, f"disk save failed: {exc}") from exc

    # --- DB 登録 ------------------------------------------------------------
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

    # --- STT タスク投入 ------------------------------------------------------
    task = transcribe_file.delay(file_id)

    return {"file_id": file_id, "task_id": task.id}
