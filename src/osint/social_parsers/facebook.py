"""Facebook platform parser for public posts.

Extracts post metadata from public Facebook posts.
Note: Facebook requires authentication for most content.
This parser works best with public pages and posts.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..models import SocialPost

logger = logging.getLogger("traceface.osint.parsers.facebook")

# Facebook URL patterns
FACEBOOK_PATTERNS = [
    r"(?:https?://)?(?:www\.|m\.)?facebook\.com/([\w.-]+)/posts/(\d+)",
    r"(?:https?://)?(?:www\.|m\.)?facebook\.com/([\w.-]+)/photos/.*",
    r"(?:https?://)?(?:www\.|m\.)?facebook\.com/permalink\.php\?story_fbid=(\d+)",
    r"(?:https?://)?(?:www\.|m\.)?fb\.watch/(\w+)",
    r"(?:https?://)?(?:www\.|m\.)?facebook\.com/([\w.-]+)/videos/(\d+)",
]


def extract_post_id(url: str) -> str | None:
    """Extract Facebook post ID from URL.

    Args:
        url: Facebook URL

    Returns:
        Post ID or None
    """
    for pattern in FACEBOOK_PATTERNS:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1) if len(match.groups()) == 1 else match.group(2)
    return None


def fetch(url: str, timeout: float = 15.0) -> SocialPost | None:
    """Parse Facebook post metadata.

    Args:
        url: Facebook post URL
        timeout: Request timeout

    Returns:
        SocialPost with metadata, or None on failure

    Note:
        Facebook heavily restricts unauthenticated scraping.
        This parser uses OpenGraph tags which work for public pages.
        Consider using authenticated session cookies for better results.
    """
    import httpx
    from bs4 import BeautifulSoup

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
        }

        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)

        if response.status_code != 200:
            logger.debug("Facebook fetch failed: HTTP %d", response.status_code)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract OpenGraph metadata
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        og_description = soup.find("meta", property="og:description")
        og_site_name = soup.find("meta", property="og:site_name")

        title = og_title.get("content", "") if og_title else ""
        image_url = og_image.get("content", "") if og_image else ""
        description = og_description.get("content", "") if og_description else ""

        # Try to extract author/page name from URL
        author_match = re.search(r"facebook\.com/([\w.-]+)/", url)
        author_handle = f"@{author_match.group(1)}" if author_match else ""

        # Try to get better author from page title
        if not author_handle:
            title_tag = soup.find("title")
            if title_tag:
                # Format: "Page Name - Home" or similar
                parts = title_tag.get_text().split("-")
                if parts:
                    author_handle = f"@{parts[0].strip().replace(' ', '').lower()}"

        return SocialPost(
            platform="facebook",
            post_url=url,
            author_handle=author_handle,
            author_display_name=author_handle.replace("@", ""),
            post_text=title or description,
            media_url=image_url,
            timestamp="",
        )

    except Exception as exc:
        logger.debug("Facebook parse error for %s: %s", url, exc)
        return None


__all__ = ["fetch", "extract_post_id"]
