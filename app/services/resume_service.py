# app/services/resume_service.py
"""Resume business logic."""
from __future__ import annotations

import uuid
import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.resume import Resume

logger = logging.getLogger(__name__)


def activate_resume(db: Session, user_id: uuid.UUID, new_resume_id: uuid.UUID | None = None):
    """
    Deactivate all resumes for a user, then optionally activate one.
    Called before inserting a new resume so only one is active at a time.
    """
    db.execute(
        update(Resume)
        .where(Resume.user_id == user_id, Resume.is_active == True)
        .values(is_active=False)
    )
    if new_resume_id:
        db.execute(
            update(Resume)
            .where(Resume.id == new_resume_id, Resume.user_id == user_id)
            .values(is_active=True)
        )
    db.flush()
    logger.info("Activated resume %s for user %s", new_resume_id, user_id)


def get_active_resume(db: Session, user_id: uuid.UUID) -> Resume | None:
    """Return the user's currently active resume, or None."""
    return db.scalar(
        select(Resume).where(
            Resume.user_id == user_id,
            Resume.is_active == True,
        )
    )
