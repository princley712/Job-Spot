# app/api/v1/jobs.py
"""Job listing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DbSession, CurrentUser
from app.models.job import Job
from app.models.enums import JobSource
from app.schemas.job import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[JobOut])
def list_jobs(
    db: DbSession,
    user: CurrentUser,
    source: JobSource | None = None,
    remote_only: bool = False,
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    stmt = select(Job).order_by(Job.scraped_at.desc()).offset(offset).limit(limit)

    if source:
        stmt = stmt.where(Job.source == source)
    if remote_only:
        stmt = stmt.where(Job.is_remote == True)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Job.title.ilike(pattern) | Job.company.ilike(pattern))

    return list(db.scalars(stmt).all())
