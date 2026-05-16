# app/schemas/application.py
"""Pydantic schemas for Application-related API requests/responses."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ApplicationStatus
from app.schemas.job import JobBrief


class ApplicationOut(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    match_score: float | None = None
    expires_at: datetime | None = None
    applied_at: datetime | None = None
    created_at: datetime
    job: JobBrief
    skill_overlap: dict | None = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    """Request body for PATCH /applications/{id}/status"""
    status: ApplicationStatus
    note: str | None = None
