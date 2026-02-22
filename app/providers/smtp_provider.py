import smtplib
import ssl
import uuid
from email.message import EmailMessage as SMTPEmailMessage

from app.core.config import Settings
from app.providers.base import EmailMessage, ProviderAdapter, ProviderResponse


class SMTPProvider(ProviderAdapter):
    name = "smtp"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, email: EmailMessage) -> ProviderResponse:
        msg = SMTPEmailMessage()
        msg["Subject"] = email.subject
        msg["From"] = self.settings.smtp_user or "no-reply@example.com"
        msg["To"] = email.to_email
        msg.set_content(email.text_body)
        msg.add_alternative(email.html_body, subtype="html")

        try:
            if self.settings.smtp_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, context=context, timeout=15) as server:
                    if self.settings.smtp_user:
                        server.login(self.settings.smtp_user, self.settings.smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as server:
                    if self.settings.smtp_user:
                        server.login(self.settings.smtp_user, self.settings.smtp_pass)
                    server.send_message(msg)
            return ProviderResponse(
                provider_message_id=str(uuid.uuid4()),
                accepted=True,
                raw_status="accepted",
                transient=False,
            )
        except smtplib.SMTPResponseException as exc:
            transient = 400 <= exc.smtp_code < 500
            return ProviderResponse(
                provider_message_id="",
                accepted=False,
                raw_status=f"smtp_{exc.smtp_code}",
                transient=transient,
                error_code=str(exc.smtp_code),
                error_message=exc.smtp_error.decode("utf-8", errors="ignore"),
            )
        except (TimeoutError, OSError, smtplib.SMTPException) as exc:
            return ProviderResponse(
                provider_message_id="",
                accepted=False,
                raw_status="transport_error",
                transient=True,
                error_code="transport_error",
                error_message=str(exc),
            )
