from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "evalhub",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.eval_tasks"],  # registers run_evaluation + run_test_suite
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
