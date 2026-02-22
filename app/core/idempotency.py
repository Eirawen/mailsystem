from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.models import Email


class IdempotencyResult:
    def __init__(self, email: Email, reused: bool) -> None:
        self.email = email
        self.reused = reused


def create_or_reuse_email(session: Session, email: Email) -> IdempotencyResult:
    try:
        session.add(email)
        session.commit()
        session.refresh(email)
        return IdempotencyResult(email=email, reused=False)
    except IntegrityError:
        session.rollback()
        existing = session.execute(
            select(Email).where(
                Email.tenant_id == email.tenant_id,
                Email.idempotency_key == email.idempotency_key,
            )
        ).scalar_one()
        return IdempotencyResult(email=existing, reused=True)
