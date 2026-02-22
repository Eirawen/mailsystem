import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import verify_webhook_signature
from app.domain.enums import EmailStatus
from app.domain.models import Email, EmailEvent, ProviderWebhookEvent


class WebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def process_event(
        self,
        provider: str,
        payload: bytes,
        parsed_payload: dict,
        signature: str,
        timestamp: str,
        event_id: str,
    ) -> None:
        secret = self._secret_for(provider)
        verify_webhook_signature(
            payload=payload,
            provided_signature=signature,
            timestamp=timestamp,
            secret=secret,
            replay_window_seconds=self.settings.webhook_replay_window_seconds,
        )

        record = ProviderWebhookEvent(
            provider=provider,
            provider_event_id=event_id,
            tenant_id=parsed_payload.get("tenant_id"),
            signature_valid=True,
            payload_hash=hashlib.sha256(payload).hexdigest(),
        )
        self.db.add(record)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return

        email = None
        if parsed_payload.get("email_id"):
            email = self.db.execute(select(Email).where(Email.id == parsed_payload["email_id"])).scalar_one_or_none()
        if not email and parsed_payload.get("provider_message_id"):
            email = self.db.execute(
                select(Email).where(Email.provider_message_id == parsed_payload["provider_message_id"])
            ).scalar_one_or_none()

        if not email:
            return

        event_type = parsed_payload.get("event_type", "")
        now = datetime.utcnow()

        if event_type == "delivered" and email.status in {EmailStatus.sent.value, EmailStatus.delivered.value}:
            email.status = EmailStatus.delivered.value
            email.delivered_at = now
        elif event_type == "opened" and email.status in {
            EmailStatus.sent.value,
            EmailStatus.delivered.value,
            EmailStatus.opened.value,
        }:
            email.status = EmailStatus.opened.value
            email.opened_at = now
        elif event_type == "failed" and email.status not in {EmailStatus.opened.value, EmailStatus.delivered.value}:
            email.status = EmailStatus.failed.value
            email.failed_at = now
            email.failure_reason = parsed_payload.get("reason", "provider_failed")
        else:
            return

        self.db.add(
            EmailEvent(
                email_id=email.id,
                tenant_id=email.tenant_id,
                event_type=event_type,
                provider=provider,
                provider_event_id=event_id,
                payload_json=parsed_payload,
            )
        )
        self.db.commit()

    def _secret_for(self, provider: str) -> str:
        if provider == "smtp":
            return self.settings.webhook_secret_smtp
        if provider == "mock":
            return self.settings.webhook_secret_mock
        raise ValueError(f"unsupported provider {provider}")
