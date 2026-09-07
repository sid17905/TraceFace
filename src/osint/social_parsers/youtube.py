"""YouTube platform parser for video thumbnails.

Extracts video metadata and thumbnail URLs from YouTube posts.
Does NOT download videos - only retrieves publicly visible thumbnails
which can be used for reverse image search.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..models import SocialPost

logger = logging.getLogger("traceface.osint.parsers.youtube")

# YouTube URL patterns
YOUTUBE_VIDEO_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
]


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats.

    Args:
        url: YouTube URL

    Returns:
        11-character video ID or None
    """
    for pattern in YOUTUBE_VIDEO_PATTERNS:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def get_thumbnail_url(video_id: str, quality: str = "maxresdefault") -> str:
    """Get thumbnail URL for a YouTube video.

    Args:
        video_id: 11-character YouTube video ID
        quality: Thumbnail quality (default, mqdefault, hqdefault, sddefault, maxresdefault)

    Returns:
        Thumbnail URL
    """
    return f"https://i.ytimg.com/vi/{video_id}/{quality}.jpg"


def fetch(url: str, timeout: float = 15.0) -> SocialPost | None:
    """Parse YouTube video metadata.

    Args:
        url: YouTube video URL
        timeout: Request timeout (unused, kept for API compatibility)

    Returns:
        SocialPost with video metadata, or None on failure
    """
    import httpx

    video_id = extract_video_id(url)
    if not video_id:
        logger.debug("Could not extract YouTube video ID from: %s", url)
        return None

    try:
        # Try to fetch video metadata from YouTube's oEmbed endpoint
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

        response = httpx.get(oembed_url, timeout=timeout, follow_redirects=True)

        if response.status_code == 200:
            data: dict[str, Any] = response.json()

            # Extract author handle from title (e.g., "Video Title - Channel Name")
            title = data.get("title", "")
            author_handle = data.get("author_name", "")
            author_display_name = author_handle

            # Get highest quality thumbnail
            media_url = get_thumbnail_url(video_id, "maxresdefault")

            return SocialPost(
                platform="youtube",
                post_url=url,
                author_handle=f"@{author_handle}" if author_handle else "",
                author_display_name=author_display_name,
                post_text=title,
                media_url=media_url,
                timestamp="",
            )
        else:
            logger.debug("YouTube oEmbed failed for %s: HTTP %d", video_id, response.status_code)

    except Exception as exc:
        logger.debug("YouTube parse error for %s: %s", url, exc)

    # Fallback: Return post with just thumbnail URL
    try:
        return SocialPost(
            platform="youtube",
            post_url=url,
            author_handle="",
            author_display_name="",
            post_text="",
            media_url=get_thumbnail_url(video_id, "hqdefault"),
            timestamp="",
        )
    except Exception as exc:
        logger.debug("YouTube fallback failed: %s", exc)
        return None


__all__ = ["fetch", "extract_video_id", "get_thumbnail_url"]
