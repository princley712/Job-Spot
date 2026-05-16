# app/api/v1/applications.py
"""
Application CRUD endpoints.
The frontend dashboard and modal flow hit these endpoints.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, CurrentUser
from app.models.application import Application
from app.models.job import JobMatch
from app.models.enums import ApplicationStatus
from app.schemas.application import ApplicationOut, ApplicationStatusUpdate
from app.services.application_service import transition_status

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/", response_model=list[ApplicationOut])
def list_applications(
    db: DbSession,
    user: CurrentUser,
    status_filter: ApplicationStatus | None = None,
):
    """
    List all applications for the current user.
    Optional ?status=pending filter.
    """
    stmt = (
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.user_id == user.id)
        .order_by(Application.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)

    apps = db.scalars(stmt).unique().all()

    # Enrich with match_score and skill_overlap from JobMatch
    results = []
    for app in apps:
        match_data = db.execute(
            select(JobMatch.match_score, JobMatch.skill_overlap).where(
                JobMatch.user_id == user.id,
                JobMatch.job_id == app.job_id,
            )
        ).first()
        
        data = ApplicationOut.model_validate(app)
        if match_data:
            data.match_score = match_data.match_score
            data.skill_overlap = match_data.skill_overlap
        results.append(data)

    return results


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: UUID, db: DbSession, user: CurrentUser):
    app = db.scalar(
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.id == application_id, Application.user_id == user.id)
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: UUID,
    body: ApplicationStatusUpdate,
    db: DbSession,
    user: CurrentUser,
):
    """
    Update the status of an application.
    This is the endpoint the frontend modal calls.
    """
    app = db.scalar(
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.id == application_id, Application.user_id == user.id)
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    transition_status(db, app, body.status, note=body.note)
    db.refresh(app)
    return app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: UUID, db: DbSession, user: CurrentUser):
    """Hard-delete an application (for 'Not Interested')."""
    app = db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,
        )
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
