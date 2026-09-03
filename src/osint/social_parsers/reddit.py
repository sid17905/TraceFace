"""Reddit submission parser (Member 2).

Reddit exposes a public JSON representation of any post by appending ``.json``
to its permalink. The pure :func:`to_json_url` and :func:`parse_reddit_json`
functions are unit-tested directly; the network fetch is best-effort.
"""

from __future__ import annotations

import html as _html
from datetime import datetime, timezone
from typing import Any

from ..models import SocialPost

_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def to_json_url(url: str) -> str:
    """Return the ``.json`` API URL for a Reddit permalink."""

    clean = url.split("?")[0].split("#")[0]
    clean = clean.removesuffix("/")
    if clean.endswith(".json"):
        return clean
    return clean + ".json"


def _epoch_to_iso(created_utc: Any) -> str:
    try:
        ts = float(created_utc)
    except (TypeError, ValueError):
        return ""
    return (
        datetime.fromtimestamp(ts, tz=timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%S")
        + "Z"
    )


def _find_post(data: Any) -> dict[str, Any] | None:
    """Locate the ``t3`` submission node in a Reddit JSON payload."""

    listings = data if isinstance(data, list) else [data]
    for listing in listings:
        if not isinstance(listing, dict):
            continue
        children = (listing.get("data") or {}).get("children") or []
        for child in children:
            if isinstance(child, dict) and child.get("kind") == "t3":
                return child.get("data") or {}
    # Fallback: some endpoints nest the post directly.
    if isinstance(data, dict) and data.get("title") is not None:
        return data
    return None


def _best_media(post: dict[str, Any]) -> str:
    direct = post.get("url_overridden_by_dest") or post.get("url") or ""
    if isinstance(direct, str) and (
        direct.lower().endswith(_IMAGE_SUFFIXES) or "i.redd.it" in direct
    ):
        return direct
    preview = post.get("preview") or {}
    images = preview.get("images") or []
    if images and isinstance(images[0], dict):
        source = images[0].get("source") or {}
        if source.get("url"):
            return _html.unescape(source["url"])
    return direct if isinstance(direct, str) else ""


def parse_reddit_json(data: Any, url: str) -> SocialPost | None:
    """Convert a Reddit ``.json`` payload into a :class:`SocialPost`."""

    post = _find_post(data)
    if post is None:
        return None

    author = (post.get("author") or "").strip()
    title = (post.get("title") or "").strip()
    selftext = (post.get("selftext") or "").strip()
    text = title if not selftext else f"{title}\n\n{selftext}"
    permalink = post.get("permalink")
    post_url = f"https://www.reddit.com{permalink}" if permalink else url

    return SocialPost(
        platform="reddit",
        post_url=post_url,
        author_handle=f"u/{author}" if author else "",
        author_display_name=author,
        post_text=text.strip(),
        published_timestamp=_epoch_to_iso(post.get("created_utc")),
        media_url=_best_media(post),
        extra={
            "subreddit": post.get("subreddit", ""),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
        },
    )


def fetch(url: str, timeout: float = 15.0) -> SocialPost | None:
    """Fetch a Reddit submission via its JSON API and parse it (best-effort)."""

    try:
        import requests  # type: ignore
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise RuntimeError("requests is not installed.") from exc
    try:
        resp = requests.get(
            to_json_url(url),
            timeout=timeout,
            headers={"User-Agent": "TraceFaceBot/1.0 (OSINT provenance)"},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:  # noqa: BLE001
        return None
    return parse_reddit_json(data, url)


__all__ = ["fetch", "parse_reddit_json", "to_json_url"]
