"""Instagram public-post parser (Member 2).

Instagram gates its private API behind authentication, so we rely on the public
OpenGraph metadata exposed on post pages (``og:image``, ``og:title``,
``og:description``). Parsing is delegated to :mod:`generic_web` and then
specialized for Instagram's title conventions.
"""

from __future__ import annotations

import re
from typing import Optional

from ..models import SocialPost
from . import generic_web

# og:title looks like: "Jane Doe (@janedoe) on Instagram: \"caption...\""
_TITLE_RE = re.compile(r"^(?P<name>.*?)\s*\(@(?P<handle>[^)]+)\)")


def parse_instagram_html(page_html: str, url: str) -> SocialPost:
    """Parse a public Instagram post page into a :class:`SocialPost`."""

    post = generic_web.parse_open_graph(page_html, url, platform="instagram")

    title = post.author_display_name or ""
    # generic_web put the article/site author in author fields; Instagram encodes
    # the real author inside og:title, so re-derive from the raw OG map.
    og = generic_web.extract_open_graph(page_html)
    og_title = og.get("og:title", "")
    match = _TITLE_RE.match(og_title)
    if match:
        post.author_display_name = match.group("name").strip()
        post.author_handle = "@" + match.group("handle").strip()
    elif og_title:
        post.author_display_name = og_title.split(" on Instagram")[0].strip()

    caption = og.get("og:description") or post.post_text
    post.post_text = caption.strip()
    post.media_url = og.get("og:image", post.media_url)
    post.platform = "instagram"
    return post


def fetch(url: str, timeout: float = 15.0) -> Optional[SocialPost]:
    """Fetch a public Instagram post and parse its OpenGraph metadata."""

    try:
        import requests  # type: ignore
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise RuntimeError("requests is not installed.") from exc
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TraceFaceBot/1.0)"},
        )
        resp.raise_for_status()
    except Exception:
        return None
    return parse_instagram_html(resp.text, url)


__all__ = ["parse_instagram_html", "fetch"]
