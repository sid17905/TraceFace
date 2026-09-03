"""OpenGraph / JSON-LD metadata extractor for generic web pages (Member 2).

Many social posts are embedded in news articles and blogs that expose Schema.org
metadata. This module harvests ``og:*`` / ``article:*`` meta tags and
``application/ld+json`` blocks.

``beautifulsoup4`` is used when available for robust parsing, but a
regex-based fallback keeps the pure ``extract_*`` / ``parse_*`` functions working
(and unit-testable) with only the standard library.
"""

from __future__ import annotations

import html as _html
import json
import re
from typing import Any, Optional

from ..models import SocialPost

# Regexes tolerate either attribute order: property/name before or after content.
_META_A = re.compile(
    r"""<meta\s+[^>]*?(?:property|name)\s*=\s*["']([^"']+)["'][^>]*?"""
    r"""content\s*=\s*["']([^"']*)["']""",
    re.IGNORECASE,
)
_META_B = re.compile(
    r"""<meta\s+[^>]*?content\s*=\s*["']([^"']*)["'][^>]*?"""
    r"""(?:property|name)\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
_LD_JSON = re.compile(
    r"""<script[^>]*type\s*=\s*["']application/ld\+json["'][^>]*>(.*?)</script>""",
    re.IGNORECASE | re.DOTALL,
)


def _regex_meta(page_html: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for key, content in _META_A.findall(page_html):
        found.setdefault(key.strip().lower(), _html.unescape(content.strip()))
    for content, key in _META_B.findall(page_html):
        found.setdefault(key.strip().lower(), _html.unescape(content.strip()))
    return found


def extract_open_graph(page_html: str) -> dict[str, str]:
    """Return a ``{meta-key: content}`` map (keys lowercased, e.g. ``og:image``)."""

    if not page_html:
        return {}
    try:  # optional dependency — richer parsing when installed
        from bs4 import BeautifulSoup  # type: ignore

        soup = BeautifulSoup(page_html, "html.parser")
        found: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if key and content is not None:
                found.setdefault(key.strip().lower(), content.strip())
        return found or _regex_meta(page_html)
    except Exception:
        return _regex_meta(page_html)


def extract_json_ld(page_html: str) -> list[dict[str, Any]]:
    """Return parsed JSON-LD blocks; malformed blocks are skipped."""

    blocks: list[dict[str, Any]] = []
    for raw in _LD_JSON.findall(page_html or ""):
        try:
            parsed = json.loads(raw.strip())
        except (ValueError, TypeError):
            continue
        if isinstance(parsed, list):
            blocks.extend(b for b in parsed if isinstance(b, dict))
        elif isinstance(parsed, dict):
            blocks.append(parsed)
    return blocks


def _first_json_ld_value(blocks: list[dict[str, Any]], *keys: str) -> str:
    for block in blocks:
        for key in keys:
            val = block.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, dict):
                name = val.get("name")
                if isinstance(name, str) and name:
                    return name
    return ""


def parse_open_graph(page_html: str, url: str, platform: str = "generic") -> SocialPost:
    """Build a :class:`SocialPost` from OpenGraph + JSON-LD signals."""

    og = extract_open_graph(page_html)
    ld = extract_json_ld(page_html)

    title = og.get("og:title") or _first_json_ld_value(ld, "headline", "name")
    image = og.get("og:image") or og.get("og:image:url") or _first_json_ld_value(ld, "image")
    published = (
        og.get("article:published_time")
        or og.get("og:updated_time")
        or _first_json_ld_value(ld, "datePublished", "dateCreated")
    )
    author = (
        og.get("article:author")
        or og.get("og:site_name")
        or _first_json_ld_value(ld, "author", "publisher")
    )
    description = og.get("og:description") or _first_json_ld_value(ld, "description")

    return SocialPost(
        platform=platform,
        post_url=og.get("og:url") or url,
        author_handle=author,
        author_display_name=author,
        post_text=(title or description or "").strip(),
        published_timestamp=published,
        media_url=image,
        extra={"description": description} if description else {},
    )


def fetch(url: str, timeout: float = 15.0) -> Optional[SocialPost]:
    """Fetch a web page and parse its OpenGraph/JSON-LD metadata (best-effort)."""

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
    return parse_open_graph(resp.text, url)


__all__ = [
    "extract_open_graph",
    "extract_json_ld",
    "parse_open_graph",
    "fetch",
]
