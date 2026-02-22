from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep
from app.domain.schemas import BulkSendRequest, BulkSendResponse
from app.services.bulk_service import BulkService

router = APIRouter(tags=["bulk"])


@router.post("/send/bulk", response_model=BulkSendResponse, status_code=status.HTTP_202_ACCEPTED)
def send_bulk(payload: BulkSendRequest, db: Session = Depends(db_session_dep)):
    if not payload.recipients:
        raise HTTPException(status_code=400, detail="recipients cannot be empty")

    service = BulkService(db)
    job = service.enqueue_bulk(payload)
    return BulkSendResponse(bulk_id=job.id, queued_count=job.total_count)
