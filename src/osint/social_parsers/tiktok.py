"""TikTok platform parser for video posts.

Extracts video metadata and thumbnail URLs from TikTok posts.
Uses web scraping as TikTok doesn't provide public API.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..models import SocialPost

logger = logging.getLogger("traceface.osint.parsers.tiktok")

# TikTok URL patterns
TIKTOK_PATTERNS = [
    r"(?:https?://)?(?:www\.)?tiktok\.com/@[\w.-]+/video/(\d+)",
    r"(?:https?://)?(?:vm\.)?tiktok\.com/(\w+)",
    r"(?:https?://)?(?:www\.)?tiktok\.com/t/(\w+)",
]


def extract_video_id(url: str) -> str | None:
    """Extract TikTok video ID from URL.

    Args:
        url: TikTok URL

    Returns:
        Video ID or None
    """
    for pattern in TIKTOK_PATTERNS:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def fetch(url: str, timeout: float = 15.0) -> SocialPost | None:
    """Parse TikTok video metadata using web scraping.

    Args:
        url: TikTok video URL
        timeout: Request timeout

    Returns:
        SocialPost with video metadata, or None on failure
    """
    import httpx
    from bs4 import BeautifulSoup

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)

        if response.status_code != 200:
            logger.debug("TikTok fetch failed: HTTP %d", response.status_code)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract OpenGraph metadata
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        og_description = soup.find("meta", property="og:description")

        title = og_title.get("content", "") if og_title else ""
        thumbnail_url = og_image.get("content", "") if og_image else ""
        description = og_description.get("content", "") if og_description else ""

        # Try to extract author from URL
        author_match = re.search(r"@([\w.-]+)/video/", url)
        author_handle = f"@{author_match.group(1)}" if author_match else ""

        # Try LD-JSON for more metadata
        ld_json_script = soup.find("script", type="application/ld+json")
        if ld_json_script:
            try:
                import json
                ld_data: dict[str, Any] = json.loads(ld_json_script.string)
                if not author_handle and "author" in ld_data:
                    author_handle = f"@{ld_data['author'].get('name', '')}"
            except Exception:
                pass

        return SocialPost(
            platform="tiktok",
            post_url=url,
            author_handle=author_handle,
            author_display_name=author_handle.replace("@", ""),
            post_text=title or description,
            media_url=thumbnail_url,
            timestamp="",
        )

    except Exception as exc:
        logger.debug("TikTok parse error for %s: %s", url, exc)
        return None


__all__ = ["fetch", "extract_video_id"]
