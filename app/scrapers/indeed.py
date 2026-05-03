# app/scrapers/indeed.py
"""
Indeed job-search scraper.
Target URL format:
  https://www.indeed.com/jobs?q=python+developer&l=Remote
"""
from __future__ import annotations

import logging
from playwright.async_api import Page

from app.models.enums import JobSource
from app.scrapers.base import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_external_id

logger = logging.getLogger(__name__)

INDEED_BASE = "https://www.indeed.com"


class IndeedScraper(BaseScraper):
    SOURCE = JobSource.INDEED

    async def _extract_listings(self, page: Page, url: str) -> list[ScrapedJob]:
        results: list[ScrapedJob] = []

        # Wait for result cards to render
        await page.wait_for_selector("div.job_seen_beacon", timeout=10_000).catch(lambda _: None)

        cards = await page.query_selector_all("div.job_seen_beacon")
        if not cards:
            cards = await page.query_selector_all("div.jobsearch-ResultsList > div")

        logger.info("[indeed] Found %d job cards on page", len(cards))

        for card in cards:
            try:
                # ── Title ──
                title_el = await card.query_selector("h2.jobTitle span[title]")
                if not title_el:
                    title_el = await card.query_selector("h2.jobTitle a")
                title = (await title_el.inner_text()).strip() if title_el else ""

                # ── Company ──
                company_el = await card.query_selector("[data-testid='company-name']")
                if not company_el:
                    company_el = await card.query_selector("span.companyName")
                company = (await company_el.inner_text()).strip() if company_el else ""

                # ── Location ──
                loc_el = await card.query_selector("[data-testid='text-location']")
                if not loc_el:
                    loc_el = await card.query_selector("div.companyLocation")
                location = (await loc_el.inner_text()).strip() if loc_el else None

                # ── Link ──
                link_el = await card.query_selector("h2.jobTitle a")
                href = (await link_el.get_attribute("href")) if link_el else ""
                if href and not href.startswith("http"):
                    href = f"{INDEED_BASE}{href}"

                # ── Snippet / description ──
                snippet_el = await card.query_selector("div.job-snippet")
                snippet = (await snippet_el.inner_text()).strip() if snippet_el else ""

                if not title or not href:
                    continue

                is_remote = bool(location and "remote" in location.lower())

                results.append(ScrapedJob(
                    title=title,
                    company=company,
                    description=snippet or f"{title} at {company}",
                    apply_url=href,
                    canonical_url=href,
                    external_id=extract_external_id(href, "indeed"),
                    source=self.SOURCE,
                    location=location,
                    is_remote=is_remote,
                    raw_payload={"source_url": url},
                ))

            except Exception:
                logger.exception("[indeed] Error parsing a card")
                continue

        return results
