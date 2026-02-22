from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mailsystem",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_default_queue="mail.send",
    task_routes={
        "app.queue.tasks_send.process_email_task": {"queue": "mail.send"},
        "app.queue.tasks_bulk.process_bulk_task": {"queue": "mail.bulk"},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
