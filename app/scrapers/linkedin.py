# app/scrapers/linkedin.py
"""
LinkedIn job-search scraper.
Target URL format:
  https://www.linkedin.com/jobs/search/?keywords=python+developer&location=Remote
"""
from __future__ import annotations

import logging
from playwright.async_api import Page

from app.models.enums import JobSource
from app.scrapers.base import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_external_id

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    SOURCE = JobSource.LINKEDIN

    async def _extract_listings(self, page: Page, url: str) -> list[ScrapedJob]:
        results: list[ScrapedJob] = []

        # Scroll to load lazy-rendered cards
        await self._scroll_to_bottom(page, pause=1.0, max_scrolls=10)

        cards = await page.query_selector_all("ul.jobs-search__results-list > li")
        if not cards:
            # Fallback selector for guest/public view
            cards = await page.query_selector_all("li.result-card")

        logger.info("[linkedin] Found %d job cards on page", len(cards))

        for card in cards:
            try:
                # ── Title ──
                title_el = await card.query_selector("h3.base-search-card__title")
                title = (await title_el.inner_text()).strip() if title_el else ""

                # ── Company ──
                company_el = await card.query_selector("h4.base-search-card__subtitle")
                company = (await company_el.inner_text()).strip() if company_el else ""

                # ── Location ──
                loc_el = await card.query_selector("span.job-search-card__location")
                location = (await loc_el.inner_text()).strip() if loc_el else None

                # ── Link ──
                link_el = await card.query_selector("a.base-card__full-link")
                href = (await link_el.get_attribute("href")) if link_el else ""
                href = href.strip() if href else ""

                if not title or not href:
                    continue

                is_remote = bool(location and "remote" in location.lower())

                results.append(ScrapedJob(
                    title=title,
                    company=company,
                    description=f"{title} at {company}",  # full desc requires detail page
                    apply_url=href,
                    canonical_url=href,
                    external_id=extract_external_id(href, "linkedin"),
                    source=self.SOURCE,
                    location=location,
                    is_remote=is_remote,
                    raw_payload={"source_url": url},
                ))

            except Exception:
                logger.exception("[linkedin] Error parsing a card")
                continue

        return results
