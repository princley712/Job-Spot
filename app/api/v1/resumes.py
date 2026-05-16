# app/api/v1/resumes.py
"""Resume upload and management endpoints."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlalchemy import select

from app.api.deps import DbSession, CurrentUser
from app.models.resume import Resume
from app.schemas.resume import ResumeOut, ResumeUploadResponse
from app.parsers.resume_parser import parse_resume_text
from app.services.resume_service import activate_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])

UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_TYPES = {"application/pdf", "text/plain"}


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    """Upload a resume (PDF or TXT), parse it, and store the results."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    # Save file to disk
    file_id = uuid.uuid4()
    ext = ".pdf" if "pdf" in (file.content_type or "") else ".txt"
    filename = f"{file_id}{ext}"
    file_path = UPLOAD_DIR / filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse the resume
    parsed = parse_resume_text(content, file.content_type or "text/plain")

    # Deactivate previous resumes
    activate_resume(db, user.id, new_resume_id=None)

    resume = Resume(
        user_id=user.id,
        file_url=str(file_path),
        file_name=file.filename or filename,
        mime_type=file.content_type or "application/octet-stream",
        is_active=True,
        raw_text=parsed["text"],
        parsed_data=parsed["data"],
        years_experience=parsed.get("years_experience"),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeUploadResponse(
        id=resume.id,
        file_name=resume.file_name,
        extracted_skills=parsed["data"].get("skills", []),
        years_experience=parsed.get("years_experience"),
    )


@router.get("/", response_model=list[ResumeOut])
def list_resumes(db: DbSession, user: CurrentUser):
    """List all resumes for the current user."""
    resumes = db.scalars(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
    ).all()
    return list(resumes)


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: uuid.UUID, db: DbSession, user: CurrentUser):
    resume = db.scalar(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
