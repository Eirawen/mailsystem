import hashlib

from app.providers.base import EmailMessage, ProviderAdapter, ProviderResponse


class MockProvider(ProviderAdapter):
    name = "mock"

    def send(self, email: EmailMessage) -> ProviderResponse:
        digest = hashlib.sha256(f"{email.email_id}:{email.to_email}".encode("utf-8")).hexdigest()
        if email.to_email.endswith("@fail.example"):
            return ProviderResponse(
                provider_message_id="",
                accepted=False,
                raw_status="mock_failed",
                transient=False,
                error_code="mock_failure",
                error_message="forced failure domain",
            )

        return ProviderResponse(
            provider_message_id=digest[:24],
            accepted=True,
            raw_status="mock_sent",
            transient=False,
        )
