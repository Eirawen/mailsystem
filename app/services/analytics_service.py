from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Email, EmailEvent


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self, tenant_id: str, from_dt, to_dt, group_by: str, template_id: str | None = None) -> dict:
        where = [Email.tenant_id == tenant_id, Email.created_at >= from_dt, Email.created_at <= to_dt]
        if template_id:
            where.append(Email.template_id == template_id)

        totals_rows = self.db.execute(
            select(Email.status, func.count(Email.id)).where(*where).group_by(Email.status)
        ).all()
        totals = {status: count for status, count in totals_rows}

        sent = totals.get("sent", 0) + totals.get("delivered", 0) + totals.get("opened", 0)
        delivered = totals.get("delivered", 0) + totals.get("opened", 0)
        opened = totals.get("opened", 0)

        rates = {
            "delivery_rate": (delivered / sent) if sent else 0.0,
            "open_rate": (opened / delivered) if delivered else 0.0,
        }

        bucket = func.date_trunc("hour" if group_by == "hour" else "day", EmailEvent.event_time)
        events_q = (
            select(bucket.label("bucket"), EmailEvent.event_type, func.count(EmailEvent.id))
            .where(EmailEvent.tenant_id == tenant_id, EmailEvent.event_time >= from_dt, EmailEvent.event_time <= to_dt)
            .group_by(bucket, EmailEvent.event_type)
            .order_by(bucket)
        )
        series_rows = self.db.execute(events_q).all()

        series = [{"bucket": str(row[0]), "event_type": row[1], "count": row[2]} for row in series_rows]
        return {"totals": totals, "rates": rates, "series": series}
