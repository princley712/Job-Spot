# app/api/v1/redirects.py
"""
Redirect endpoint: logs the click and sends the user to the external apply page.
GET /apply/{application_id}  →  logs redirect  →  302 to external URL
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, CurrentUser
from app.models.application import Application, RedirectLog

router = APIRouter(tags=["redirects"])


@router.get("/apply/{application_id}")
def apply_redirect(
    application_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
):
    """
    1. Look up the application and its job.
    2. Log the redirect (IP, user-agent, timestamp).
    3. Update last_redirect_at on the application.
    4. 302 redirect to the external apply URL.
    """
    app = db.scalar(
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.id == application_id, Application.user_id == user.id)
    )
    if not app or not app.job:
        raise HTTPException(status_code=404, detail="Application not found")

    # Log the redirect
    log = RedirectLog(
        application_id=app.id,
        target_url=app.job.apply_url,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(log)

    app.last_redirect_at = datetime.now(timezone.utc)
    db.commit()

    return RedirectResponse(url=app.job.apply_url, status_code=302)
