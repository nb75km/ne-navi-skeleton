"""Celery task の状態を問い合わせるエンドポイント"""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from shared.celery_app import celery_app   # ← Celery インスタンス

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs/{task_id}")
def get_job(task_id: str):
    """
    • 202 <PENDING> | 200 <SUCCESS|FAILURE|…> を返す
      （PENDING 時のみ 202 にしておくとフロントは分岐しやすい）
    """
    res = AsyncResult(task_id, app=celery_app)
    if res is None:                       # ID フォーマットは正しいが見つからない
        raise HTTPException(404, "Not Found")

    payload = {
        "task_id": task_id,
        "state": res.state,               # PENDING / STARTED / SUCCESS / FAILURE …
        "result": res.result if res.successful() else None,
    }
    return payload if res.state == "SUCCESS" else (payload, 202)
