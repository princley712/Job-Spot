# app/scrapers/utils.py
"""
Shared utilities for all scrapers: rate-limiting, content hashing, deduplication,
and proxy rotation helpers.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import random
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job

logger = logging.getLogger(__name__)


# ── Rate Limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Simple async token-bucket rate limiter.
    Ensures a minimum `delay` seconds between requests, with optional jitter
    so multiple concurrent scrapers don't fire in lockstep.
    """

    def __init__(self, delay: float = 2.0, jitter: float = 0.5):
        self._delay = delay
        self._jitter = jitter
        self._lock = asyncio.Lock()
        self._last: float = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait_for = self._delay + random.uniform(0, self._jitter) - (now - self._last)
            if wait_for > 0:
                logger.debug("Rate-limiter sleeping %.2fs", wait_for)
                await asyncio.sleep(wait_for)
            self._last = asyncio.get_event_loop().time()


# ── Content Hashing ───────────────────────────────────────────────────────────

def content_hash(title: str, company: str, description: str) -> str:
    """
    SHA-256 of normalised title+company+description.
    Used as the dedup key so re-scraping the same listing is idempotent.
    """
    blob = f"{title.strip().lower()}|{company.strip().lower()}|{description.strip().lower()}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── Deduplication ─────────────────────────────────────────────────────────────

def is_duplicate(db: Session, hash_value: str) -> bool:
    """Check if a job with this content_hash already exists."""
    return db.scalar(select(Job.id).where(Job.content_hash == hash_value)) is not None


def deduplicate_batch(db: Session, jobs: list[dict]) -> list[dict]:
    """
    Given a list of raw scraped job dicts (must contain 'content_hash'),
    return only the ones not already in the DB.
    """
    if not jobs:
        return []

    hashes = [j["content_hash"] for j in jobs]
    existing = set(
        db.scalars(select(Job.content_hash).where(Job.content_hash.in_(hashes))).all()
    )
    new_jobs = [j for j in jobs if j["content_hash"] not in existing]
    logger.info("Dedup: %d total → %d new, %d skipped", len(jobs), len(new_jobs), len(jobs) - len(new_jobs))
    return new_jobs


# ── URL Helpers ───────────────────────────────────────────────────────────────

def normalise_url(url: str) -> str:
    """Strip tracking params & fragments so the same listing doesn't appear twice."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def extract_external_id(url: str, source: str) -> str:
    """
    Best-effort extraction of a board-native job ID from the URL.
    Falls back to a hash of the full URL.
    """
    path = urlparse(url).path.rstrip("/")

    if source == "greenhouse":
        # https://boards.greenhouse.io/company/jobs/12345
        parts = path.split("/")
        if "jobs" in parts:
            idx = parts.index("jobs")
            if idx + 1 < len(parts):
                return parts[idx + 1]

    if source == "lever":
        # https://jobs.lever.co/company/uuid
        parts = path.split("/")
        if len(parts) >= 3:
            return parts[-1]

    # Fallback: hash the URL
    return hashlib.md5(url.encode()).hexdigest()[:16]


# ── Proxy Rotation ────────────────────────────────────────────────────────────

class ProxyRotator:
    """
    Round-robin proxy rotator.  Accepts a list of proxy URLs or a single one.
    Returns None (direct connect) when no proxies are configured.
    """

    def __init__(self, proxies: list[str] | str | None = None):
        if proxies is None:
            self._proxies: list[str] = []
        elif isinstance(proxies, str):
            self._proxies = [proxies]
        else:
            self._proxies = list(proxies)
        self._idx = 0

    def next(self) -> dict | None:
        """Return Playwright-compatible proxy dict or None."""
        if not self._proxies:
            return None
        proxy_url = self._proxies[self._idx % len(self._proxies)]
        self._idx += 1
        parsed = urlparse(proxy_url)
        result: dict = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            result["username"] = parsed.username
        if parsed.password:
            result["password"] = parsed.password
        return result
