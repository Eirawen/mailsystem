from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session_dep
from app.domain.schemas import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    tenant_id: str,
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    group_by: str = Query(default="day", pattern="^(day|hour)$"),
    template_id: str | None = None,
    db: Session = Depends(db_session_dep),
):
    now = datetime.utcnow()
    from_dt = from_dt or (now - timedelta(days=7))
    to_dt = to_dt or now

    data = AnalyticsService(db).summary(tenant_id=tenant_id, from_dt=from_dt, to_dt=to_dt, group_by=group_by, template_id=template_id)
    return AnalyticsResponse.model_validate(data)
