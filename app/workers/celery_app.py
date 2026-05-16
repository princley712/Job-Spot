from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()
celery_app = Celery(
    "jobtracker", 
    broker=settings.CELERY_BROKER_URL, 
    backend=settings.CELERY_RESULT_BACKEND
)

# ── Auto-discover tasks from all worker modules ──────────────
celery_app.autodiscover_tasks(["app.workers.scraper_tasks", "app.workers.matcher_tasks", "app.workers.janitor"])

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# ── Beat Schedule ────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Expire PENDING/NOT_APPLIED applications older than 7 days — runs hourly
    "expire-stale-apps": {
        "task": "janitor.expire_stale_applications",
        "schedule": crontab(minute=0),
    },
    # Scrape all configured job boards — runs every 6 hours
    "scrape-jobs": {
        "task": "scraper.run_all_sources",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Match new jobs against all user resumes — runs 15 min after each scrape
    "match-new-jobs": {
        "task": "matcher.match_all_users",
        "schedule": crontab(minute=15, hour="*/6"),
    },
}
