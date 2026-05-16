# app/schemas/resume.py
"""Pydantic schemas for Resume-related API requests/responses."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: UUID
    user_id: UUID
    file_name: str
    mime_type: str
    is_active: bool
    years_experience: int | None = None
    parsed_skills: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    id: UUID
    file_name: str
    extracted_skills: list[str]
    years_experience: int | None = None
    message: str = "Resume parsed successfully"
