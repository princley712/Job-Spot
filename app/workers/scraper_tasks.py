# app/workers/scraper_tasks.py
"""
Celery tasks that orchestrate the scraping pipeline.

Flow:
  1. `run_all_sources` (scheduled every 6h by beat) dispatches per-source tasks.
  2. Each `scrape_source` task spins up the right Playwright scraper,
     collects ScrapedJob DTOs, deduplicates, and bulk-inserts into the DB.
  3. After insert it fans out to `trigger_matching` so new jobs are scored
     against every active resume.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from celery import shared_task

from app.db.session import SessionLocal
from app.models.enums import JobSource
from app.scrapers.base import ScrapedJob
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.indeed import IndeedScraper
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.services.job_service import save_scraped_jobs

logger = logging.getLogger(__name__)

# ── Registry: source enum → (scraper class, default search URLs) ──────────

SCRAPER_REGISTRY: dict[JobSource, tuple[type, list[str]]] = {
    JobSource.LINKEDIN: (
        LinkedInScraper,
        [
            "https://www.linkedin.com/jobs/search/?keywords=python+developer&location=Remote&f_WT=2",
            "https://www.linkedin.com/jobs/search/?keywords=backend+engineer&location=Remote&f_WT=2",
        ],
    ),
    JobSource.INDEED: (
        IndeedScraper,
        [
            "https://www.indeed.com/jobs?q=python+developer&l=Remote&fromage=3",
            "https://www.indeed.com/jobs?q=backend+engineer&l=Remote&fromage=3",
        ],
    ),
    JobSource.GREENHOUSE: (
        GreenhouseScraper,
        [
            # Add company board URLs here
            # "https://boards.greenhouse.io/stripe",
            # "https://boards.greenhouse.io/figma",
        ],
    ),
    JobSource.LEVER: (
        LeverScraper,
        [
            # "https://jobs.lever.co/netlify",
            # "https://jobs.lever.co/vercel",
        ],
    ),
}


# ── Async runner helper ───────────────────────────────────────────────────────

def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Inside an already-running loop (rare in Celery workers)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@shared_task(name="scraper.run_all_sources", bind=True, max_retries=1)
def run_all_sources(self) -> dict[str, Any]:
    """
    Fan-out task: dispatches a `scrape_source` task for every registered source.
    Scheduled by Celery Beat (see celery_app.py).
    """
    dispatched = {}
    for source in SCRAPER_REGISTRY:
        scraper_cls, urls = SCRAPER_REGISTRY[source]
        if not urls:
            logger.info("Skipping %s — no URLs configured", source.value)
            continue
        result = scrape_source.delay(source.value, urls)
        dispatched[source.value] = result.id
        logger.info("Dispatched scrape_source for %s (task_id=%s)", source.value, result.id)

    return {"dispatched": dispatched}


@shared_task(name="scraper.scrape_source", bind=True, max_retries=2, default_retry_delay=60)
def scrape_source(self, source_value: str, urls: list[str]) -> dict[str, Any]:
    """
    Scrape a single source and persist new jobs.

    Parameters
    ----------
    source_value : str
        The JobSource enum value (e.g. "linkedin").
    urls : list[str]
        Target search / board URLs to scrape.
    """
    source = JobSource(source_value)
    scraper_cls, _ = SCRAPER_REGISTRY[source]
    scraper = scraper_cls()

    try:
        logger.info("[%s] Starting scrape of %d URLs", source.value, len(urls))

        # Run the async Playwright scraper
        scraped: list[ScrapedJob] = _run_async(scraper.scrape(urls))
        logger.info("[%s] Scraped %d raw listings", source.value, len(scraped))

        if not scraped:
            return {"source": source.value, "scraped": 0, "saved": 0}

        # Convert to dicts and persist
        raw_dicts = [job.to_dict() for job in scraped]

        with SessionLocal() as db:
            inserted = save_scraped_jobs(db, raw_dicts)

        saved_count = len(inserted)
        logger.info("[%s] Saved %d new jobs", source.value, saved_count)

        # Trigger matching for new jobs
        if saved_count > 0:
            from app.workers.matcher_tasks import match_new_jobs_for_all_users
            match_new_jobs_for_all_users.delay()

        return {
            "source": source.value,
            "scraped": len(scraped),
            "saved": saved_count,
        }

    except Exception as exc:
        logger.exception("[%s] Scrape failed", source.value)
        raise self.retry(exc=exc)


@shared_task(name="scraper.scrape_custom_urls")
def scrape_custom_urls(source_value: str, urls: list[str]) -> dict[str, Any]:
    """
    One-off task to scrape user-supplied URLs.
    Useful from the `manual_scrape.py` script or an admin endpoint.
    """
    return scrape_source(source_value, urls)
