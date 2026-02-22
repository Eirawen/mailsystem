from enum import StrEnum


class TenantStatus(StrEnum):
    active = "active"
    disabled = "disabled"


class EmailStatus(StrEnum):
    queued = "queued"
    scheduled = "scheduled"
    processing = "processing"
    sent = "sent"
    delivered = "delivered"
    opened = "opened"
    failed = "failed"


class EventType(StrEnum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    opened = "opened"
    failed = "failed"
    retry_scheduled = "retry_scheduled"
    dead_lettered = "dead_lettered"


class BulkStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    complete = "complete"
    failed = "failed"
