from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep, redis_dep, settings_dep
from app.core.config import Settings
from app.core.rate_limit import RateLimitExceededError, RateLimiter
from app.domain.schemas import SendRequest, SendResponse
from app.queue.tasks_send import process_email_task
from app.services.mail_service import MailService

router = APIRouter(tags=["send"])


@router.post("/send", response_model=SendResponse, status_code=status.HTTP_202_ACCEPTED)
def send_email(
    payload: SendRequest,
    db: Session = Depends(db_session_dep),
    settings: Settings = Depends(settings_dep),
    redis_client: Redis = Depends(redis_dep),
):
    limiter = RateLimiter(redis_client, settings.rate_limit_window_seconds)
    provider = payload.provider_hint or settings.default_provider
    try:
        limiter.check_tenant(payload.tenant_id, settings.rate_limit_tenant_per_window)
        limiter.check_provider(payload.tenant_id, provider, settings.rate_limit_provider_per_window)
    except RateLimitExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    service = MailService(db)
    try:
        email, reused = service.enqueue_send(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not reused:
        if email.status == "scheduled" and email.scheduled_at is not None:
            process_email_task.apply_async(args=[email.id], eta=email.scheduled_at, queue="mail.scheduled")
        else:
            process_email_task.apply_async(args=[email.id], queue="mail.send")

    return SendResponse(email_id=email.id, status=email.status, idempotency_reused=reused)
