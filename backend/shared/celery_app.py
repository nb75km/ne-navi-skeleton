import os
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "ne_navi",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/1"),
    include=[
        "shared.etl_dify",
        "shared.draft_minutes",  # Minutes draft task
        "shared.stt_transcribe",
    ],
)

# ---- periodic tasks (example) ---------------------------------------------
celery_app.conf.beat_schedule = {
    "sync-dify-15min": {
        "task": "etl.sync_dify",
        "schedule": 900,  # 15 min
    },
}
