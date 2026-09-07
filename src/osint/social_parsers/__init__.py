"""Social-media parser package (Member 2).

Exposes :func:`detect_platform` (URL → internal platform key) and
:func:`parse_post` (URL → :class:`~src.osint.models.SocialPost`), routing each
URL to the correct platform parser. Individual pure ``parse_*`` functions live
in the per-platform modules and are used directly by the unit tests.

Uses the dynamic PlatformRegistry for extensible platform support.
"""

from __future__ import annotations

from ..models import SocialPost
from .platform_registry import get_platform_registry, PlatformRegistry

def detect_platform(url: str) -> str:
    """Classify a URL into one of the known platform keys, else ``"generic"``."""
    registry = get_platform_registry()
    return registry.detect_platform(url)


def parse_post(url: str, timeout: float = 15.0) -> SocialPost | None:
    """Fetch and parse a post from any supported platform (best-effort)."""
    registry = get_platform_registry()
    return registry.parse_post(url, timeout=timeout)


def get_fetcher(platform: str):
    """Get the fetcher function for a platform."""
    registry = get_platform_registry()
    return registry.get_fetcher(platform)


__all__ = [
    "detect_platform",
    "parse_post",
    "get_platform_registry",
    "get_fetcher",
    "PlatformRegistry",
]
