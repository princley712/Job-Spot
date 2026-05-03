# app/workers/matcher_tasks.py
"""
Celery tasks for resume ↔ job matching.

Flow:
  1. `match_new_jobs_for_all_users` — iterates all users with an active resume,
     finds jobs they haven't been scored against, and runs the matching engine.
  2. `match_jobs_for_user` — scores a single user's resume against unmatched jobs.
  3. Results are written to the `job_matches` table and, if above threshold,
     an Application row is auto-created in PENDING status.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select

from app.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import ApplicationStatus
from app.models.job import Job, JobMatch
from app.models.resume import Resume, Skill
from app.models.application import Application
from app.models.user import User
from app.services.job_service import get_unmatched_jobs
from app.services.matching_service import MatchingEngine

logger = logging.getLogger(__name__)
settings = get_settings()


def _load_known_skills(db) -> set[str]:
    """Load the canonical skill dictionary from DB."""
    return set(db.scalars(select(Skill.name)).all())


@shared_task(name="matcher.match_all_users")
def match_new_jobs_for_all_users() -> dict:
    """
    Iterate every user who has at least one active resume and score them
    against jobs they haven't seen yet.
    """
    with SessionLocal() as db:
        users_with_resumes = db.scalars(
            select(User.id).where(
                User.is_active == True,
                User.id.in_(
                    select(Resume.user_id).where(Resume.is_active == True)
                ),
            )
        ).all()

    results = {}
    for user_id in users_with_resumes:
        r = match_jobs_for_user.delay(str(user_id))
        results[str(user_id)] = r.id

    logger.info("Dispatched matching for %d users", len(results))
    return {"dispatched_users": len(results)}


@shared_task(name="matcher.match_for_user", bind=True, max_retries=2, default_retry_delay=30)
def match_jobs_for_user(self, user_id_str: str) -> dict:
    """
    Score all un-matched jobs for a single user's active resume.

    Steps:
      1. Load user's active resume text.
      2. Fetch jobs not yet in `job_matches` for this user.
      3. Run MatchingEngine.score_jobs().
      4. Write JobMatch rows.
      5. Auto-create Application rows (PENDING) for matches above threshold.
    """
    user_id = uuid.UUID(user_id_str)

    with SessionLocal() as db:
        # ── 1. Load resume ────────────────────────────────────
        resume = db.scalar(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.is_active == True,
            ).order_by(Resume.created_at.desc())
        )
        if not resume or not resume.raw_text:
            logger.warning("User %s has no active resume with text — skipping", user_id)
            return {"user_id": user_id_str, "matched": 0, "reason": "no_resume"}

        # ── 2. Fetch unmatched jobs ───────────────────────────
        jobs = get_unmatched_jobs(db, user_id, limit=500)
        if not jobs:
            logger.info("User %s — no new jobs to match", user_id)
            return {"user_id": user_id_str, "matched": 0, "reason": "no_new_jobs"}

        job_dicts = [
            {
                "id": str(j.id),
                "title": j.title,
                "description": j.description,
                "requirements": j.requirements or "",
            }
            for j in jobs
        ]

        # ── 3. Score ──────────────────────────────────────────
        known_skills = _load_known_skills(db)
        engine = MatchingEngine(known_skills=known_skills)
        matches = engine.score_jobs(resume.raw_text, job_dicts)

        # ── 4. Write JobMatch + Application rows ──────────────
        created = 0
        for m in matches:
            job_uuid = uuid.UUID(m.job_id)

            # JobMatch row
            jm = JobMatch(
                user_id=user_id,
                job_id=job_uuid,
                resume_id=resume.id,
                match_score=m.score,
                skill_overlap={
                    "matched": m.matched_skills,
                    "missing": m.missing_skills,
                },
            )
            db.add(jm)

            # Auto-create Application in PENDING so it appears on the user's dashboard
            existing_app = db.scalar(
                select(Application).where(
                    Application.user_id == user_id,
                    Application.job_id == job_uuid,
                )
            )
            if not existing_app:
                app = Application(
                    user_id=user_id,
                    job_id=job_uuid,
                    resume_id=resume.id,
                    status=ApplicationStatus.PENDING,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=settings.APPLICATION_EXPIRY_DAYS),
                )
                db.add(app)

            created += 1

        db.commit()
        logger.info("User %s — %d matches created (from %d jobs)", user_id, created, len(jobs))

        return {
            "user_id": user_id_str,
            "jobs_evaluated": len(jobs),
            "matched": created,
            "top_score": matches[0].score if matches else 0,
        }
