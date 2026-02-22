from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Recipient(BaseModel):
    email: EmailStr
    name: str | None = None


class SendRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=64)
    recipient: Recipient
    template_id: str
    variables: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provider_hint: str | None = None
    send_at: datetime | None = None
    idempotency_key: str = Field(min_length=1, max_length=128)


class SendResponse(BaseModel):
    email_id: str
    status: str
    idempotency_reused: bool


class BulkRecipient(BaseModel):
    email: EmailStr
    name: str | None = None


class BulkSendRequest(BaseModel):
    tenant_id: str
    template_id: str
    recipients: list[BulkRecipient]
    shared_variables: dict[str, Any] = Field(default_factory=dict)
    per_recipient_variables: dict[str, dict[str, Any]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    batch_size: int = Field(default=100, ge=1, le=1000)
    provider_hint: str | None = None
    send_at: datetime | None = None
    idempotency_key: str


class BulkSendResponse(BaseModel):
    bulk_id: str
    queued_count: int


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    recipient_email: str
    recipient_name: str | None
    template_id: str
    provider_name: str
    provider_message_id: str | None
    status: str
    attempt_count: int
    failure_reason: str | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    delivered_at: datetime | None
    opened_at: datetime | None
    failed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WebhookEventPayload(BaseModel):
    tenant_id: str | None = None
    email_id: str | None = None
    provider_message_id: str | None = None
    event_type: str
    occurred_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AnalyticsResponse(BaseModel):
    totals: dict[str, int]
    rates: dict[str, float]
    series: list[dict[str, Any]]
