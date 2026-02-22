from app.db.session import get_session_factory
from app.queue.celery_app import celery_app
from app.services.mail_service import MailService


@celery_app.task(name="app.queue.tasks_send.process_email_task", bind=True, max_retries=0)
def process_email_task(self, email_id: str):
    db = get_session_factory()()
    try:
        MailService(db).process_email(email_id)
    finally:
        db.close()
