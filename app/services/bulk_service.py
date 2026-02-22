from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import BulkStatus
from app.domain.models import BulkJob
from app.domain.schemas import BulkSendRequest, SendRequest
from app.services.mail_service import MailService


class BulkService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def enqueue_bulk(self, request: BulkSendRequest) -> BulkJob:
        bulk_job = BulkJob(
            tenant_id=request.tenant_id,
            template_id=request.template_id,
            total_count=len(request.recipients),
            queued_count=0,
            status=BulkStatus.queued.value,
        )
        self.db.add(bulk_job)
        self.db.commit()
        self.db.refresh(bulk_job)

        from app.queue.tasks_bulk import process_bulk_task

        process_bulk_task.delay(bulk_job.id, request.model_dump(mode="json"))
        return bulk_job

    def process_bulk(self, bulk_id: str, payload: dict) -> int:
        bulk_job = self.db.execute(select(BulkJob).where(BulkJob.id == bulk_id)).scalar_one()
        bulk_job.status = BulkStatus.processing.value
        self.db.commit()

        request = BulkSendRequest.model_validate(payload)
        mail_service = MailService(self.db)
        queued = 0

        for recipient in request.recipients:
            vars_for_recipient = dict(request.shared_variables)
            vars_for_recipient.update(request.per_recipient_variables.get(str(recipient.email), {}))

            send_req = SendRequest(
                tenant_id=request.tenant_id,
                recipient=recipient,
                template_id=request.template_id,
                variables=vars_for_recipient,
                metadata=request.metadata,
                provider_hint=request.provider_hint,
                send_at=request.send_at,
                idempotency_key=f"{request.idempotency_key}:{recipient.email}",
            )
            email, reused = mail_service.enqueue_send(send_req)
            if not reused:
                from app.queue.tasks_send import process_email_task

                if email.status == "scheduled" and email.scheduled_at is not None:
                    process_email_task.apply_async(args=[email.id], eta=email.scheduled_at, queue="mail.scheduled")
                else:
                    process_email_task.apply_async(args=[email.id], queue="mail.send")
                queued += 1

        bulk_job.queued_count = queued
        bulk_job.status = BulkStatus.complete.value
        self.db.commit()
        return queued
