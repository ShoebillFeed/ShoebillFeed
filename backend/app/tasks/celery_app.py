from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "shoebill_feed",
    broker=settings.redis_url,
    backend=settings.redis_url.replace("/0", "/1"),
    include=[
        "app.tasks.fetch_tasks",
        "app.tasks.process_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=700,
    task_time_limit=900,
    beat_schedule={
        "fetch-all-sources": {
            "task": "app.tasks.fetch_tasks.fetch_all_sources",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "fetch"},
        },
        "batch-process-unprocessed": {
            "task": "app.tasks.process_tasks.batch_process_unprocessed",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "process"},
        },
        "poll-llm-batches": {
            "task": "app.tasks.process_tasks.poll_llm_batches",
            "schedule": crontab(minute="*/2"),
            "options": {"queue": "process"},
        },
        "cleanup-old-items": {
            "task": "app.tasks.fetch_tasks.cleanup_old_items",
            "schedule": crontab(hour=3, minute=0),
            "options": {"queue": "default"},
        },
    },
)
