#!/usr/bin/env python
# scripts/manual_scrape.py
"""
CLI helper to trigger a one-off scrape without Celery.

Usage:
    # Scrape LinkedIn with default URLs
    python -m scripts.manual_scrape linkedin

    # Scrape Greenhouse with custom board URLs
    python -m scripts.manual_scrape greenhouse \
        https://boards.greenhouse.io/stripe \
        https://boards.greenhouse.io/figma

    # Scrape and also run matching for a specific user
    python -m scripts.manual_scrape indeed --match-user <USER_UUID>
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.db.session import SessionLocal
from app.models.enums import JobSource
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.indeed import IndeedScraper
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.services.job_service import save_scraped_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("manual_scrape")

SCRAPER_MAP = {
    "linkedin":    LinkedInScraper,
    "indeed":      IndeedScraper,
    "greenhouse":  GreenhouseScraper,
    "lever":       LeverScraper,
}

DEFAULT_URLS = {
    "linkedin": [
        "https://www.linkedin.com/jobs/search/?keywords=python+developer&location=Remote&f_WT=2",
    ],
    "indeed": [
        "https://www.indeed.com/jobs?q=python+developer&l=Remote&fromage=3",
    ],
    "greenhouse": [],
    "lever": [],
}


def main():
    parser = argparse.ArgumentParser(description="Manual job scraper")
    parser.add_argument("source", choices=list(SCRAPER_MAP.keys()), help="Job board to scrape")
    parser.add_argument("urls", nargs="*", help="Target URLs (uses defaults if omitted)")
    parser.add_argument("--match-user", type=str, default=None, help="UUID of user to match after scrape")
    args = parser.parse_args()

    urls = args.urls or DEFAULT_URLS.get(args.source, [])
    if not urls:
        logger.error("No URLs provided and no defaults for '%s'. Pass URLs as positional args.", args.source)
        sys.exit(1)

    scraper_cls = SCRAPER_MAP[args.source]
    scraper = scraper_cls()

    logger.info("Scraping %s with %d URL(s)...", args.source, len(urls))
    scraped = asyncio.run(scraper.scrape(urls))
    logger.info("Extracted %d raw listings", len(scraped))

    if not scraped:
        logger.info("Nothing to save.")
        return

    raw_dicts = [job.to_dict() for job in scraped]

    with SessionLocal() as db:
        inserted = save_scraped_jobs(db, raw_dicts)
        logger.info("Persisted %d new jobs (skipped %d duplicates)", len(inserted), len(scraped) - len(inserted))

    # Optional: trigger matching
    if args.match_user:
        from app.workers.matcher_tasks import match_jobs_for_user
        logger.info("Triggering matching for user %s...", args.match_user)
        result = match_jobs_for_user(args.match_user)
        logger.info("Matching result: %s", result)


if __name__ == "__main__":
    main()
