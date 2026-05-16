# app/scrapers/lever.py
"""
Lever ATS board scraper.
Target URL format:
  https://jobs.lever.co/{company_slug}
"""
from __future__ import annotations

import logging
from playwright.async_api import Page

from app.models.enums import JobSource
from app.scrapers.base import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_external_id

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    SOURCE = JobSource.LEVER

    async def _extract_listings(self, page: Page, url: str) -> list[ScrapedJob]:
        results: list[ScrapedJob] = []

        try:
            await page.wait_for_selector("div.posting", timeout=10_000)
        except Exception:
            pass

        postings = await page.query_selector_all("div.posting")
        logger.info("[lever] Found %d postings", len(postings))

        # Derive company from URL slug
        slug_parts = url.rstrip("/").split("/")
        company_slug = slug_parts[-1] if slug_parts else "unknown"
        company_name = company_slug.replace("-", " ").title()

        for posting in postings:
            try:
                # ── Title ──
                title_el = await posting.query_selector("h5[data-qa='posting-name']")
                if not title_el:
                    title_el = await posting.query_selector("a.posting-title h5")
                title = (await title_el.inner_text()).strip() if title_el else ""

                # ── Link ──
                link_el = await posting.query_selector("a.posting-btn-submit")
                if not link_el:
                    link_el = await posting.query_selector("a.posting-title")
                href = (await link_el.get_attribute("href")) if link_el else ""
                href = href.strip() if href else ""

                # ── Location + Work Type ──
                loc_el = await posting.query_selector("span.sort-by-location")
                location = (await loc_el.inner_text()).strip() if loc_el else None

                worktype_el = await posting.query_selector("span.sort-by-commitment")
                worktype = (await worktype_el.inner_text()).strip() if worktype_el else ""

                if not title or not href:
                    continue

                is_remote = bool(
                    (location and "remote" in location.lower())
                    or (worktype and "remote" in worktype.lower())
                )

                results.append(ScrapedJob(
                    title=title,
                    company=company_name,
                    description=f"{title} at {company_name} — {worktype}".strip(" —"),
                    apply_url=href,
                    canonical_url=href,
                    external_id=extract_external_id(href, "lever"),
                    source=self.SOURCE,
                    location=location,
                    is_remote=is_remote,
                    raw_payload={"source_url": url, "commitment": worktype},
                ))

            except Exception:
                logger.exception("[lever] Error parsing a posting")
                continue

        return results
