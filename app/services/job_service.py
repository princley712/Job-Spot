# app/services/job_service.py
"""
Persistence layer for scraped jobs.
Handles upsert (insert-or-skip-if-exists) and batch saving.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.enums import JobSource
from app.scrapers.utils import deduplicate_batch

logger = logging.getLogger(__name__)


def upsert_job(db: Session, data: dict) -> Job | None:
    """
    Insert a single job if its content_hash doesn't already exist.
    Returns the Job instance on insert, None on duplicate.
    """
    existing = db.scalar(
        select(Job).where(Job.content_hash == data["content_hash"])
    )
    if existing:
        logger.debug("Skipping duplicate job: %s @ %s", data["title"], data["company"])
        return None

    job = Job(
        source=data["source"],
        external_id=data["external_id"],
        apply_url=data["apply_url"],
        canonical_url=data["canonical_url"],
        content_hash=data["content_hash"],
        title=data["title"],
        company=data["company"],
        location=data.get("location"),
        is_remote=data.get("is_remote", False),
        employment_type=data.get("employment_type"),
        description=data["description"],
        requirements=data.get("requirements"),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        salary_currency=data.get("salary_currency", "USD"),
        posted_at=data.get("posted_at"),
        scraped_at=data.get("scraped_at", datetime.now(timezone.utc)),
        raw_payload=data.get("raw_payload", {}),
    )
    db.add(job)
    return job


def save_scraped_jobs(db: Session, raw_jobs: list[dict]) -> list[Job]:
    """
    Batch-save scraped jobs.

    1. Deduplicates against existing DB rows (by content_hash).
    2. Inserts only new jobs.
    3. Commits once at the end.

    Returns the list of newly inserted Job objects.
    """
    new_data = deduplicate_batch(db, raw_jobs)
    inserted: list[Job] = []

    for data in new_data:
        job = upsert_job(db, data)
        if job:
            inserted.append(job)

    if inserted:
        db.commit()
        logger.info("Saved %d new jobs to database", len(inserted))
    else:
        logger.info("No new jobs to save")

    return inserted


def get_unmatched_jobs(db: Session, user_id: str, limit: int = 500) -> list[Job]:
    """
    Return jobs that this user hasn't been matched with yet.
    Used by the matcher task to score new jobs for a user.
    """
    from app.models.job import JobMatch  # local import to avoid circular

    subq = (
        select(JobMatch.job_id)
        .where(JobMatch.user_id == user_id)
        .scalar_subquery()
    )
    stmt = (
        select(Job)
        .where(Job.id.notin_(subq))
        .order_by(Job.scraped_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
