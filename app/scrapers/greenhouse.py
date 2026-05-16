# app/scrapers/greenhouse.py
"""
Greenhouse ATS board scraper.
Target URL format:
  https://boards.greenhouse.io/{company_slug}
"""
from __future__ import annotations

import logging
from playwright.async_api import Page

from app.models.enums import JobSource
from app.scrapers.base import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_external_id

logger = logging.getLogger(__name__)

GH_BASE = "https://boards.greenhouse.io"


class GreenhouseScraper(BaseScraper):
    SOURCE = JobSource.GREENHOUSE

    async def _extract_listings(self, page: Page, url: str) -> list[ScrapedJob]:
        results: list[ScrapedJob] = []

        try:
            await page.wait_for_selector("section.level-0", timeout=10_000)
        except Exception:
            pass

        # Greenhouse boards group openings by department
        rows = await page.query_selector_all("div.opening")
        logger.info("[greenhouse] Found %d openings", len(rows))

        for row in rows:
            try:
                link_el = await row.query_selector("a")
                if not link_el:
                    continue

                title = (await link_el.inner_text()).strip()
                href = (await link_el.get_attribute("href")) or ""
                if href and not href.startswith("http"):
                    href = f"{GH_BASE}{href}"

                loc_el = await row.query_selector("span.location")
                location = (await loc_el.inner_text()).strip() if loc_el else None

                # Extract company name from the page heading
                company = await self._safe_text(page, "span.company-name", default="")
                if not company:
                    # Fallback: derive from URL slug
                    parts = url.rstrip("/").split("/")
                    company = parts[-1].replace("-", " ").title() if parts else "Unknown"

                is_remote = bool(location and "remote" in location.lower())

                results.append(ScrapedJob(
                    title=title,
                    company=company,
                    description=f"{title} at {company}",
                    apply_url=href,
                    canonical_url=href,
                    external_id=extract_external_id(href, "greenhouse"),
                    source=self.SOURCE,
                    location=location,
                    is_remote=is_remote,
                    raw_payload={"source_url": url},
                ))

            except Exception:
                logger.exception("[greenhouse] Error parsing an opening")
                continue

        return results
