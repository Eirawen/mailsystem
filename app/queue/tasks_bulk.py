from app.db.session import get_session_factory
from app.queue.celery_app import celery_app
from app.services.bulk_service import BulkService


@celery_app.task(name="app.queue.tasks_bulk.process_bulk_task", bind=True, max_retries=0)
def process_bulk_task(self, bulk_id: str, payload: dict):
    db = get_session_factory()()
    try:
        BulkService(db).process_bulk(bulk_id=bulk_id, payload=payload)
    finally:
        db.close()
