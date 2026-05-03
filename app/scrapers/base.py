# app/scrapers/base.py
"""
Abstract base class for all job board scrapers.
Each concrete scraper implements `_extract_listings` which returns raw dicts;
the base class handles browser lifecycle, rate-limiting, hashing, and result
normalisation.
"""
from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.config import get_settings
from app.models.enums import JobSource
from app.scrapers.utils import RateLimiter, ProxyRotator, content_hash, normalise_url

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Scraped job DTO ───────────────────────────────────────────────────────────

@dataclass
class ScrapedJob:
    """Normalised output that every scraper must produce."""
    title: str
    company: str
    description: str
    apply_url: str
    canonical_url: str
    external_id: str
    source: JobSource
    location: str | None = None
    is_remote: bool = False
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "USD"
    posted_at: datetime | None = None
    requirements: str | None = None
    raw_payload: dict = field(default_factory=dict)

    # Computed after init
    content_hash: str = ""

    def __post_init__(self):
        self.apply_url = normalise_url(self.apply_url)
        self.canonical_url = normalise_url(self.canonical_url)
        if not self.content_hash:
            self.content_hash = content_hash(self.title, self.company, self.description)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "apply_url": self.apply_url,
            "canonical_url": self.canonical_url,
            "external_id": self.external_id,
            "source": self.source,
            "location": self.location,
            "is_remote": self.is_remote,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "posted_at": self.posted_at,
            "requirements": self.requirements,
            "raw_payload": self.raw_payload,
            "content_hash": self.content_hash,
            "scraped_at": datetime.now(timezone.utc),
        }


# ── Abstract Base ─────────────────────────────────────────────────────────────

class BaseScraper(abc.ABC):
    """
    Lifecycle
    ---------
    1. `scrape(urls)` opens a Playwright browser.
    2. For each URL it calls `_extract_listings(page, url)` (implemented by subclass).
    3. Results are normalised into `ScrapedJob` dataclasses and returned.

    Subclass contract
    -----------------
    * Set `SOURCE` class var to the matching `JobSource` enum.
    * Implement `_extract_listings(page, url) -> list[ScrapedJob]`.
    """

    SOURCE: JobSource  # override in each subclass

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        proxy_rotator: ProxyRotator | None = None,
    ):
        self._limiter = rate_limiter or RateLimiter(delay=settings.SCRAPER_REQUEST_DELAY_S)
        self._proxy = proxy_rotator or ProxyRotator(settings.SCRAPER_PROXY)

    # ── Public API ────────────────────────────────────────────

    async def scrape(self, urls: list[str]) -> list[ScrapedJob]:
        """
        Scrape a list of target URLs and return normalised ScrapedJob objects.
        Manages the full Playwright browser lifecycle internally.
        """
        all_jobs: list[ScrapedJob] = []

        async with async_playwright() as pw:
            proxy = self._proxy.next()
            browser: Browser = await pw.chromium.launch(
                headless=settings.SCRAPER_HEADLESS,
                proxy=proxy,
            )
            context: BrowserContext = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
            )
            context.set_default_timeout(settings.SCRAPER_TIMEOUT_MS)

            page: Page = await context.new_page()

            for url in urls:
                try:
                    await self._limiter.wait()
                    logger.info("[%s] Scraping %s", self.SOURCE.value, url)
                    await page.goto(url, wait_until="domcontentloaded")
                    listings = await self._extract_listings(page, url)
                    all_jobs.extend(listings)
                    logger.info("[%s] Extracted %d listings from %s", self.SOURCE.value, len(listings), url)
                except Exception:
                    logger.exception("[%s] Failed to scrape %s", self.SOURCE.value, url)

            await browser.close()

        return all_jobs

    # ── Subclass hook ─────────────────────────────────────────

    @abc.abstractmethod
    async def _extract_listings(self, page: Page, url: str) -> list[ScrapedJob]:
        """
        Given a fully-loaded Playwright page, extract all visible job listings
        and return them as ScrapedJob objects.
        """
        ...

    # ── Helpers available to subclasses ───────────────────────

    async def _safe_text(self, page: Page, selector: str, default: str = "") -> str:
        """Extract inner text from a selector; return default if missing."""
        el = await page.query_selector(selector)
        if el is None:
            return default
        return (await el.inner_text()).strip()

    async def _safe_attr(self, page: Page, selector: str, attr: str, default: str = "") -> str:
        """Extract an attribute value from a selector; return default if missing."""
        el = await page.query_selector(selector)
        if el is None:
            return default
        val = await el.get_attribute(attr)
        return (val or default).strip()

    async def _scroll_to_bottom(self, page: Page, pause: float = 0.8, max_scrolls: int = 15):
        """Incrementally scroll to trigger infinite-scroll loaders."""
        for _ in range(max_scrolls):
            prev_height = await page.evaluate("document.body.scrollHeight")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(int(pause * 1000))
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                break
