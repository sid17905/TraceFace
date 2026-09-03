"""Social-media parser package (Member 2).

Exposes :func:`detect_platform` (URL → internal platform key) and
:func:`parse_post` (URL → :class:`~src.osint.models.SocialPost`), routing each
URL to the correct platform parser. Individual pure ``parse_*`` functions live
in the per-platform modules and are used directly by the unit tests.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional  # noqa: F401

from ..models import SocialPost
from . import generic_web, instagram, reddit, twitter

# Substring → internal platform key. Order matters (check specific hosts first).
_PLATFORM_HOSTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("twitter.com", "x.com"), "twitter"),
    (("reddit.com", "redd.it"), "reddit"),
    (("instagram.com",), "instagram"),
    (("linkedin.com",), "linkedin"),
)


def detect_platform(url: str) -> str:
    """Classify a URL into one of the known platform keys, else ``"generic"``."""

    low = (url or "").lower()
    for hosts, key in _PLATFORM_HOSTS:
        if any(host in low for host in hosts):
            return key
    return "generic"


# platform key → fetch(url, timeout) -> Optional[SocialPost]
_FETCHERS: dict[str, Callable[..., SocialPost | None]] = {
    "twitter": twitter.fetch,
    "reddit": reddit.fetch,
    "instagram": instagram.fetch,
    "linkedin": generic_web.fetch,
    "generic": generic_web.fetch,
}


def get_fetcher(platform: str) -> Callable[..., SocialPost | None]:
    return _FETCHERS.get(platform, generic_web.fetch)


def parse_post(url: str, timeout: float = 15.0) -> SocialPost | None:
    """Fetch and parse a post from any supported platform (best-effort)."""

    return get_fetcher(detect_platform(url))(url, timeout=timeout)


__all__ = [
    "detect_platform",
    "generic_web",
    "get_fetcher",
    "instagram",
    "parse_post",
    "reddit",
    "twitter",
]
