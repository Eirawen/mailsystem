from dataclasses import dataclass


@dataclass(slots=True)
class EmailMessage:
    email_id: str
    tenant_id: str
    to_email: str
    to_name: str | None
    subject: str
    html_body: str
    text_body: str
    metadata: dict


@dataclass(slots=True)
class ProviderResponse:
    provider_message_id: str
    accepted: bool
    raw_status: str
    transient: bool
    error_code: str | None = None
    error_message: str | None = None


class ProviderAdapter:
    name = "base"

    def send(self, email: EmailMessage) -> ProviderResponse:
        raise NotImplementedError
