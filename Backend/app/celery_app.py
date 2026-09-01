import os

from celery import Celery


redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise RuntimeError(
        "REDIS_URL is required to configure the AssistantAI Celery broker."
    )

celery_app = Celery(
    "assistantai",
    broker=redis_url,
    include=["app.tasks.documents"],
)
celery_app.conf.task_ignore_result = True
