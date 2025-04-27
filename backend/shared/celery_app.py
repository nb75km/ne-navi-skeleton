from celery import Celery

celery_app = Celery("ne_navi", broker="redis://redis:6379/0")

@celery_app.task
def ping():
    return "pong"
