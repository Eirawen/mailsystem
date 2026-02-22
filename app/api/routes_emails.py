from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep
from app.domain.models import Email
from app.domain.schemas import EmailResponse

router = APIRouter(tags=["emails"])


@router.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(email_id: str, tenant_id: str, db: Session = Depends(db_session_dep)):
    email = db.execute(select(Email).where(Email.id == email_id, Email.tenant_id == tenant_id)).scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="email not found")
    return EmailResponse.model_validate(email)
