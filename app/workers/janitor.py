# app/workers/janitor.py
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy import select, and_
from app.db.session import SessionLocal
from app.models.application import Application, ApplicationEvent
from app.models.enums import ApplicationStatus

EXPIRABLE = (ApplicationStatus.PENDING, ApplicationStatus.NOT_APPLIED)

@shared_task(name="janitor.expire_stale_applications")
def expire_stale_applications() -> int:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        stmt = select(Application).where(
            and_(
                Application.status.in_(EXPIRABLE),
                Application.expires_at <= now,
            )
        )
        stale = db.scalars(stmt).all()
        for app in stale:
            db.add(ApplicationEvent(
                application_id=app.id,
                from_status=app.status,
                to_status=ApplicationStatus.EXPIRED,
                note="Auto-expired after 7 days of inactivity.",
                metadata_json={"source": "system", "job": "janitor"},
            ))
            app.status = ApplicationStatus.EXPIRED
            app.expires_at = None
        db.commit()
        return len(stale)
