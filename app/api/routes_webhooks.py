import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep
from app.services.webhook_service import WebhookService

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/{provider}")
async def provider_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(db_session_dep),
    x_signature: str = Header(alias="X-Signature"),
    x_timestamp: str = Header(alias="X-Timestamp"),
    x_event_id: str = Header(alias="X-Event-Id"),
):
    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid json") from exc

    service = WebhookService(db)
    try:
        service.process_event(
            provider=provider,
            payload=body,
            parsed_payload=payload,
            signature=x_signature,
            timestamp=x_timestamp,
            event_id=x_event_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"ok": True}
