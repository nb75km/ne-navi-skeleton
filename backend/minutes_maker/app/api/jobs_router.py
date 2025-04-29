from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import SessionLocal  # sync Session maker
from ..db import models as M
from shared.celery_app import celery_app

# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_db() -> Session:  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Pydantic schema  (FastAPI が response_model に必須)
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DRAFT_READY = "DRAFT_READY"
    FAILED = "FAILED"

class JobOut(BaseModel):
    id: str
    task_id: str
    transcript_id: int | None
    status: JobStatus
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True          # ← SQLAlchemy Row → Pydantic dict

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["jobs"])

# --- DB-backed endpoints ----------------------------------------------------

@router.get("/jobs", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    """最新順でジョブ一覧を取得"""
    return db.query(M.Job).order_by(M.Job.created_at.desc()).all()


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """ジョブ詳細"""
    job = db.get(M.Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# --- legacy Celery polling (kept for compatibility) ------------------------

@router.get("/tasks/{task_id}")
def get_task_state(task_id: str):
    """
    旧 API 互換: Celery `AsyncResult` の状態を返す。
    完了前なら 202 (Accepted) を返し、クライアント側はポーリングを継続。
    """
    res = AsyncResult(task_id, app=celery_app)
    if res is None:
        raise HTTPException(404, "Unknown task id")

    payload = {
        "task_id": task_id,
        "state": res.state,
        "result": res.result if res.successful() else None,
    }
    # `res.state in ("PENDING", "STARTED", "RETRY", ...)`
    return payload if res.successful() else (payload, status.HTTP_202_ACCEPTED)
