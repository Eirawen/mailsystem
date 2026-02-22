from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Email


class MailRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, email_id: str) -> Email | None:
        return self.db.execute(select(Email).where(Email.id == email_id)).scalar_one_or_none()

    def get_by_provider_message_id(self, provider_message_id: str) -> Email | None:
        return self.db.execute(
            select(Email).where(Email.provider_message_id == provider_message_id)
        ).scalar_one_or_none()
