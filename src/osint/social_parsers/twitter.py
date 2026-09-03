"""X / Twitter post parser (Member 2).

Uses Twitter's public **syndication** endpoint (``cdn.syndication.twimg.com``),
which returns a JSON payload for a public tweet without authentication. The
pure :func:`extract_tweet_id` and :func:`parse_syndication_json` functions are
unit-tested directly; the network fetch is best-effort.
"""

from __future__ import annotations

import math
import re
from typing import Any, Optional

from ..models import SocialPost

_STATUS_RE = re.compile(r"(?:twitter\.com|x\.com)/[^/]+/status(?:es)?/(\d+)", re.IGNORECASE)
_BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def extract_tweet_id(url: str) -> Optional[str]:
    """Pull the numeric status id out of a tweet URL."""

    if not url:
        return None
    match = _STATUS_RE.search(url)
    return match.group(1) if match else None


def _to_base36(num: float, frac_digits: int = 12) -> str:
    integer = int(num)
    frac = num - integer
    if integer == 0:
        int_str = "0"
    else:
        chars = []
        n = integer
        while n > 0:
            chars.append(_BASE36[n % 36])
            n //= 36
        int_str = "".join(reversed(chars))
    frac_chars = []
    for _ in range(frac_digits):
        frac *= 36
        digit = int(frac)
        frac_chars.append(_BASE36[digit])
        frac -= digit
    return int_str + "." + "".join(frac_chars)


def syndication_token(tweet_id: str) -> str:
    """Replicate Twitter's client-side token derivation for the syndication API."""

    value = (int(tweet_id) / 1e15) * math.pi
    encoded = _to_base36(value)
    # Twitter strips runs of zeros and the decimal point.
    return encoded.replace("0", "").replace(".", "")


def syndication_url(tweet_id: str) -> str:
    return (
        "https://cdn.syndication.twimg.com/tweet-result"
        f"?id={tweet_id}&token={syndication_token(tweet_id)}&lang=en"
    )


def _extract_media(data: dict[str, Any]) -> str:
    details = data.get("mediaDetails")
    if isinstance(details, list):
        for item in details:
            if isinstance(item, dict) and item.get("media_url_https"):
                return item["media_url_https"]
    photos = data.get("photos")
    if isinstance(photos, list):
        for item in photos:
            if isinstance(item, dict) and item.get("url"):
                return item["url"]
    return ""


def parse_syndication_json(data: dict[str, Any], url: str) -> SocialPost:
    """Convert a syndication ``tweet-result`` payload into a :class:`SocialPost`."""

    user = data.get("user") or {}
    screen_name = (user.get("screen_name") or "").strip()
    handle = f"@{screen_name}" if screen_name else ""
    verified = bool(user.get("verified") or user.get("is_blue_verified"))

    return SocialPost(
        platform="twitter",
        post_url=url,
        author_handle=handle,
        author_display_name=(user.get("name") or "").strip(),
        post_text=(data.get("text") or data.get("full_text") or "").strip(),
        published_timestamp=(data.get("created_at") or "").strip(),
        media_url=_extract_media(data),
        extra={"verified": verified, "tweet_id": str(data.get("id_str") or "")},
    )


def fetch(url: str, timeout: float = 15.0) -> Optional[SocialPost]:
    """Fetch a public tweet via the syndication API and parse it (best-effort)."""

    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        return None
    try:
        import requests  # type: ignore
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise RuntimeError("requests is not installed.") from exc
    try:
        resp = requests.get(
            syndication_url(tweet_id),
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TraceFaceBot/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None
    post = parse_syndication_json(data, url)
    post.extra.setdefault("tweet_id", tweet_id)
    return post


__all__ = [
    "extract_tweet_id",
    "syndication_token",
    "syndication_url",
    "parse_syndication_json",
    "fetch",
]
