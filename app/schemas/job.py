# app/schemas/job.py
"""Pydantic schemas for Job-related API responses."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import JobSource, EmploymentType


class JobOut(BaseModel):
    id: UUID
    source: JobSource
    title: str
    company: str
    location: str | None = None
    is_remote: bool = False
    employment_type: EmploymentType | None = None
    description: str
    requirements: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = "USD"
    apply_url: str
    canonical_url: str
    posted_at: datetime | None = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class JobBrief(BaseModel):
    """Lightweight version for list views."""
    id: UUID
    title: str
    company: str
    location: str | None = None
    is_remote: bool = False
    source: JobSource
    apply_url: str
    posted_at: datetime | None = None

    model_config = {"from_attributes": True}
