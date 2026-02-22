import logging
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.idempotency import create_or_reuse_email
from app.domain.enums import EmailStatus, EventType
from app.domain.models import DeadLetter, Email, EmailEvent, Template, Tenant
from app.domain.schemas import SendRequest
from app.providers.base import EmailMessage
from app.providers.registry import registry
from app.queue.retry_policy import compute_retry_delay
from app.templates.renderer import render_template

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def enqueue_send(self, request: SendRequest) -> tuple[Email, bool]:
        tenant = self.db.execute(
            select(Tenant).where(Tenant.id == request.tenant_id, Tenant.status == "active")
        ).scalar_one_or_none()
        if not tenant:
            raise ValueError("tenant not found or disabled")

        template = self.db.execute(
            select(Template).where(
                Template.id == request.template_id,
                Template.tenant_id == request.tenant_id,
                Template.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if not template:
            raise ValueError("template not found")

        provider = request.provider_hint or self.settings.default_provider
        status = EmailStatus.scheduled.value if request.send_at else EmailStatus.queued.value

        email = Email(
            tenant_id=request.tenant_id,
            idempotency_key=request.idempotency_key,
            recipient_email=str(request.recipient.email),
            recipient_name=request.recipient.name,
            template_id=request.template_id,
            variables_json=request.variables,
            metadata_json=request.metadata,
            provider_name=provider,
            status=status,
            scheduled_at=request.send_at,
        )

        result = create_or_reuse_email(self.db, email)
        if not result.reused:
            self._append_event(result.email, EventType.queued.value, {"scheduled": bool(request.send_at)})
            self.db.commit()

        return result.email, result.reused

    def process_email(self, email_id: str) -> None:
        email = self.db.execute(select(Email).where(Email.id == email_id)).scalar_one_or_none()
        if not email:
            logger.warning("email not found", extra={"email_id": email_id})
            return

        if email.status in {EmailStatus.sent.value, EmailStatus.delivered.value, EmailStatus.opened.value}:
            return

        claim = self.db.query(Email).filter(
            and_(Email.id == email.id, Email.status.in_([EmailStatus.queued.value, EmailStatus.scheduled.value, EmailStatus.processing.value]))
        ).update({Email.status: EmailStatus.processing.value}, synchronize_session=False)
        self.db.commit()
        if claim == 0:
            return

        email = self.db.execute(select(Email).where(Email.id == email_id)).scalar_one()
        template = self.db.execute(select(Template).where(Template.id == email.template_id)).scalar_one()
        subject, html, text = render_template(
            template.subject_template,
            template.html_template,
            template.text_template,
            email.variables_json,
        )

        provider = registry.get(email.provider_name)
        response = provider.send(
            EmailMessage(
                email_id=email.id,
                tenant_id=email.tenant_id,
                to_email=email.recipient_email,
                to_name=email.recipient_name,
                subject=subject,
                html_body=html,
                text_body=text,
                metadata=email.metadata_json,
            )
        )

        email.attempt_count += 1
        if response.accepted:
            email.status = EmailStatus.sent.value
            email.sent_at = datetime.utcnow()
            email.provider_message_id = response.provider_message_id
            email.failure_reason = None
            self._append_event(email, EventType.sent.value, {"provider_status": response.raw_status})
            self.db.commit()
            return

        if response.transient and email.attempt_count < self.settings.max_retries:
            delay = compute_retry_delay(email.attempt_count, self.settings.retry_base_seconds, self.settings.retry_max_seconds)
            email.status = EmailStatus.queued.value
            email.failure_reason = response.error_message
            email.next_retry_at = datetime.utcnow()
            self._append_event(
                email,
                EventType.retry_scheduled.value,
                {
                    "delay_seconds": delay,
                    "error": response.error_message,
                    "error_code": response.error_code,
                },
            )
            self.db.commit()
            from app.queue.tasks_send import process_email_task

            process_email_task.apply_async(args=[email.id], countdown=delay, queue="mail.send")
            return

        email.status = EmailStatus.failed.value
        email.failed_at = datetime.utcnow()
        email.failure_reason = response.error_message or response.raw_status
        self._append_event(
            email,
            EventType.failed.value,
            {"error": response.error_message, "error_code": response.error_code, "transient": response.transient},
        )
        self.db.add(
            DeadLetter(
                email_id=email.id,
                tenant_id=email.tenant_id,
                last_error=email.failure_reason,
                attempt_count=email.attempt_count,
                payload_json={"provider": email.provider_name},
            )
        )
        self._append_event(email, EventType.dead_lettered.value, {"reason": email.failure_reason})
        self.db.commit()

    def _append_event(self, email: Email, event_type: str, payload: dict) -> None:
        self.db.add(
            EmailEvent(
                email_id=email.id,
                tenant_id=email.tenant_id,
                event_type=event_type,
                provider=email.provider_name,
                payload_json=payload,
            )
        )
