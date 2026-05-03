# app/services/application_service.py
from datetime import datetime, timezone
from app.models.enums import ApplicationStatus
from app.models.application import Application, ApplicationEvent

ACTIVE_STATUSES = {ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEWING, ApplicationStatus.OFFER}

def transition_status(db, app: Application, new_status: ApplicationStatus, note: str | None = None):
    event = ApplicationEvent(
        application_id=app.id,
        from_status=app.status,
        to_status=new_status,
        note=note,
        metadata_json={"source": "user"},
    )
    app.status = new_status

    # Clear expiry once user has actually engaged
    if new_status in ACTIVE_STATUSES:
        app.expires_at = None
        if new_status == ApplicationStatus.APPLIED and app.applied_at is None:
            app.applied_at = datetime.now(timezone.utc)

    db.add(event)
    db.commit()
