"""Playwright headless-browser fallback scraper (Member 2).

Autonomous fallback for when the API engines return nothing (or no keys are
configured): drives a headless Chromium instance with rotating stealth
user-agents to run a reverse-image search on a public portal and to render
dynamic (JavaScript-heavy) social pages, then harvests candidate links from the
DOM.

``playwright`` is imported lazily so this module imports without it; the pure
link-extraction helpers are unit-tested with only the standard library.
"""

from __future__ import annotations

import asyncio
import os
import random
import re

from src.config import settings

from .models import SearchCandidate, SearchEngine
from .social_parsers import detect_platform

# Rotated to reduce anti-bot fingerprinting on public portals.
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "  # noqa: ISC004
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "  # noqa: ISC004
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "  # noqa: ISC004
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
)

_HREF_RE = re.compile(r'href\s*=\s*["\'](https?://[^"\'#]+)["\']', re.IGNORECASE)
# Search-portal / tracker hosts we never want to treat as candidate sources.
_NOISE_HOSTS = (
    "google.",
    "bing.",
    "yandex.",
    "microsoft.",
    "gstatic.",
    "w3.org",
    "schema.org",
)


def _headless_from_env() -> bool:
    if "PLAYWRIGHT_HEADLESS" in os.environ:
        return os.environ["PLAYWRIGHT_HEADLESS"].strip().lower() in ("1", "true", "yes", "t")
    return settings.playwright_headless


def extract_links(page_html: str) -> list[str]:
    """Extract unique absolute http(s) links from rendered HTML (pure)."""

    seen: set[str] = set()
    ordered: list[str] = []
    for href in _HREF_RE.findall(page_html or ""):
        if href in seen:
            continue
        seen.add(href)
        ordered.append(href)
    return ordered


def links_to_candidates(
    links: list[str], engine: str = SearchEngine.PLAYWRIGHT_FALLBACK
) -> list[SearchCandidate]:
    """Map harvested links to candidates, dropping search-portal noise and
    prioritizing social-media domains."""

    candidates: list[SearchCandidate] = []
    for link in links:
        low = link.lower()
        if any(noise in low for noise in _NOISE_HOSTS):
            continue
        candidates.append(
            SearchCandidate(
                source_url=link,
                platform=detect_platform(link),
                engine=engine,
            )
        )
    candidates.sort(key=lambda c: 0 if c.platform != "generic" else 1)
    return candidates


class PlaywrightScraper:
    """Headless Chromium automation for dynamic scraping and reverse search."""

    def __init__(
        self, headless: bool | None = None, nav_timeout_ms: int = 30000
    ) -> None:
        self.headless = _headless_from_env() if headless is None else headless
        self.nav_timeout_ms = nav_timeout_ms

    @staticmethod
    def _require_playwright():
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "playwright is not installed. Run: "
                "pip install playwright && playwright install chromium"
            ) from exc
        return async_playwright

    async def _new_context(self, browser):
        return await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )

    async def scrape_url_async(self, url: str) -> str:
        """Render a page with a real browser and return its HTML."""

        async_playwright = self._require_playwright()
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            try:
                context = await self._new_context(browser)
                page = await context.new_page()
                await page.goto(url, timeout=self.nav_timeout_ms, wait_until="domcontentloaded")
                try:
                    await page.wait_for_load_state("networkidle", timeout=self.nav_timeout_ms)
                except Exception:  # noqa: BLE001, S110
                    pass  # networkidle is best-effort on chatty pages
                return await page.content()
            finally:
                await browser.close()

    async def reverse_image_search_async(
        self, image_path: str, max_candidates: int = 10
    ) -> list[SearchCandidate]:
        """Upload a local image to a public visual-search portal and harvest links.

        Selectors on public portals change frequently; any failure degrades
        gracefully to an empty candidate list so the dispatcher can continue.
        """

        async_playwright = self._require_playwright()
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            try:
                context = await self._new_context(browser)
                page = await context.new_page()
                await page.goto(
                    "https://www.bing.com/visualsearch",
                    timeout=self.nav_timeout_ms,
                    wait_until="domcontentloaded",
                )
                try:
                    file_input = page.locator("input[type='file']").first
                    await file_input.set_input_files(image_path, timeout=self.nav_timeout_ms)
                    await page.wait_for_load_state("networkidle", timeout=self.nav_timeout_ms)
                except Exception:  # noqa: BLE001
                    return []
                html = await page.content()
            finally:
                await browser.close()

        return links_to_candidates(extract_links(html))[: max(0, max_candidates)]

    # -- blocking wrappers -------------------------------------------------

    def scrape_url(self, url: str) -> str:
        return asyncio.run(self.scrape_url_async(url))

    def reverse_image_search(
        self, image_path: str, max_candidates: int = 10
    ) -> list[SearchCandidate]:
        return asyncio.run(
            self.reverse_image_search_async(image_path, max_candidates=max_candidates)
        )


__all__ = [
    "USER_AGENTS",
    "PlaywrightScraper",
    "extract_links",
    "links_to_candidates",
]
