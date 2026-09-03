"""Google Lens reverse-image search via SerpApi (Member 2, primary engine).

The heavy ``serpapi`` client is imported lazily inside :meth:`LensSearchEngine.search`
so that importing this module — and running the unit tests, which exercise the
pure ``parse_*`` functions against fixtures — needs no network and no
third-party package installed.

Reference: docs/MEMBER_2_PLAN.md (Day 1) and docs/COMMON_REFERENCE.md §1.2.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from .models import SearchCandidate, SearchEngine, SOCIAL_DOMAINS
from .social_parsers import detect_platform


def prioritize_social(candidates: list[SearchCandidate]) -> list[SearchCandidate]:
    """Stable-sort candidates so social-media domains rank first.

    Social posts carry the richest, most citable provenance (author + timestamp),
    so we evaluate them before generic web hits. Ordering within each group is
    preserved (i.e. the engine's own relevance ranking is respected).
    """

    def _key(c: SearchCandidate) -> int:
        url = (c.source_url or "").lower()
        return 0 if any(dom in url for dom in SOCIAL_DOMAINS) else 1

    return sorted(candidates, key=_key)


def parse_serpapi_response(
    data: dict[str, Any], max_candidates: int = 10
) -> list[SearchCandidate]:
    """Convert a raw SerpApi Google Lens response into ranked candidates.

    Pure function — no network — so it is fully unit-testable with a captured
    fixture (``data/fixtures/mock_lens_response.json``). SerpApi returns visual
    hits under ``visual_matches`` with ``title``/``link``/``thumbnail``/``source``
    and sometimes a full-resolution ``image``.
    """

    matches = data.get("visual_matches") or []
    candidates: list[SearchCandidate] = []
    for m in matches:
        link = (m.get("link") or "").strip()
        if not link:
            continue
        # SerpApi exposes the full-res asset under "image" (older field) or a
        # nested "image"/"original" depending on version; be tolerant.
        media_url = ""
        img = m.get("image")
        if isinstance(img, str):
            media_url = img
        elif isinstance(img, dict):
            media_url = img.get("link") or img.get("original") or ""
        candidates.append(
            SearchCandidate(
                source_url=link,
                source_title=(m.get("title") or "").strip(),
                thumbnail_url=(m.get("thumbnail") or "").strip(),
                media_url=media_url.strip(),
                platform=detect_platform(link),
                engine=SearchEngine.GOOGLE_LENS_SERPAPI,
            )
        )

    ranked = prioritize_social(candidates)
    return ranked[: max(0, max_candidates)]


class LensSearchEngine:
    """Thin wrapper around SerpApi's ``google_lens`` engine."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("SERPAPI_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        max_candidates: int = 10,
    ) -> list[SearchCandidate]:
        """Run a Google Lens reverse-image query and return ranked candidates.

        SerpApi's Lens engine accepts a **publicly reachable image URL**. A local
        ``image_path`` must therefore be hosted first (the Playwright fallback in
        :mod:`playwright_scraper` handles raw local files instead).
        """

        if not self.is_configured:
            raise RuntimeError(
                "SERPAPI_KEY is not set — configure it in .env or pass api_key=..."
            )
        if not image_url:
            raise ValueError(
                "LensSearchEngine.search requires image_url (a public URL). "
                "For a local file use the Playwright fallback."
            )

        try:  # lazy, optional dependency
            from serpapi import GoogleSearch  # type: ignore
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "google-search-results is not installed. "
                "Run: pip install google-search-results"
            ) from exc

        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": self.api_key,
        }
        results = GoogleSearch(params).get_dict()
        return parse_serpapi_response(results, max_candidates=max_candidates)


# ---------------------------------------------------------------------------
# Secondary engine: Bing Visual Search (optional)
# ---------------------------------------------------------------------------


def parse_bing_response(
    data: dict[str, Any], max_candidates: int = 10
) -> list[SearchCandidate]:
    """Parse a Bing Visual Search API response into candidates (pure)."""

    candidates: list[SearchCandidate] = []
    for tag in data.get("tags", []) or []:
        for action in tag.get("actions", []) or []:
            value = (action.get("data") or {}).get("value") or []
            for item in value:
                host = (item.get("hostPageUrl") or "").strip()
                if not host:
                    continue
                candidates.append(
                    SearchCandidate(
                        source_url=host,
                        source_title=(item.get("name") or "").strip(),
                        thumbnail_url=(item.get("thumbnailUrl") or "").strip(),
                        media_url=(item.get("contentUrl") or "").strip(),
                        platform=detect_platform(host),
                        engine=SearchEngine.BING_VISUAL_SEARCH,
                    )
                )
    return prioritize_social(candidates)[: max(0, max_candidates)]


class BingVisualSearch:
    """Optional secondary engine. Returns ``[]`` when no API key is configured."""

    ENDPOINT = "https://api.bing.microsoft.com/v7.0/images/visualsearch"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("BING_VISUAL_SEARCH_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(
        self, image_url: str, max_candidates: int = 10
    ) -> list[SearchCandidate]:
        if not self.is_configured:
            return []
        try:  # lazy, optional dependency
            import requests  # type: ignore
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError("requests is not installed.") from exc

        resp = requests.post(
            self.ENDPOINT,
            headers={"Ocp-Apim-Subscription-Key": self.api_key},
            data={"imageInfo": f'{{"url":"{image_url}"}}'},
            timeout=15,
        )
        resp.raise_for_status()
        return parse_bing_response(resp.json(), max_candidates=max_candidates)


__all__ = [
    "LensSearchEngine",
    "BingVisualSearch",
    "parse_serpapi_response",
    "parse_bing_response",
    "prioritize_social",
]
