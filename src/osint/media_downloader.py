"""Asynchronous in-memory media downloader (Member 2).

Downloads candidate images *without touching disk*, computing the SHA-256 of the
byte stream in-flight and validating the content type (JPEG / PNG / WebP) both
from the HTTP header and from the file's magic bytes. ``httpx`` (async) and
``requests`` (sync fallback) are imported lazily, so this module and its pure
helpers import with only the standard library present.

Reference: docs/MEMBER_2_PLAN.md (Day 1, 15:00-18:00).
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Iterable
from dataclasses import dataclass

from src.config import settings

# Content types accepted for candidate media.
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_MAX_BYTES = 25 * 1024 * 1024  # 25 MiB memory-buffer cap per asset
DEFAULT_CONCURRENCY = 8

# Rotated so bulk downloads from CDNs are less likely to be throttled/blocked.
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class MediaDownloadError(RuntimeError):
    """Raised when a candidate asset cannot be fetched or is not a valid image."""


# ---------------------------------------------------------------------------
# Pure helpers (no network — unit tested directly)
# ---------------------------------------------------------------------------


def sha256_hex(data: bytes) -> str:
    """Hex SHA-256 digest of a byte buffer."""

    return hashlib.sha256(data).hexdigest()


def sniff_image_type(data: bytes) -> str | None:
    """Best-effort image content-type detection from magic bytes."""

    if len(data) < 12:
        return None
    if data[0:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[0:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def normalize_content_type(header_value: str) -> str:
    """Strip parameters/casing from a Content-Type header (``image/jpeg; q=1``)."""

    return (header_value or "").split(";")[0].strip().lower()


def validate_content_type(content_type: str) -> bool:
    return normalize_content_type(content_type) in ALLOWED_CONTENT_TYPES


def resolve_content_type(header_value: str, data: bytes) -> str | None:
    """Return a trusted content type, preferring magic-byte sniffing.

    The sniffed type wins when present (servers frequently mislabel CDN assets as
    ``application/octet-stream``); otherwise we fall back to the header.
    """

    sniffed = sniff_image_type(data)
    if sniffed:
        return sniffed
    header = normalize_content_type(header_value)
    return header if header in ALLOWED_CONTENT_TYPES else None


@dataclass
class DownloadedMedia:
    """An image fetched entirely into memory."""

    url: str
    data: bytes
    content_type: str
    sha256: str

    @property
    def size(self) -> int:
        return len(self.data)

    @classmethod
    def from_bytes(cls, url: str, data: bytes, content_type: str = "") -> DownloadedMedia:
        """Construct from an in-memory buffer (used by tests and sync paths)."""

        resolved = resolve_content_type(content_type, data)
        if resolved is None:
            raise MediaDownloadError(
                f"Unsupported or unrecognized image content for {url!r}"
            )
        return cls(url=url, data=data, content_type=resolved, sha256=sha256_hex(data))


# ---------------------------------------------------------------------------
# Async / sync downloader
# ---------------------------------------------------------------------------


class MediaDownloader:
    """Concurrent, in-memory media fetcher with strict limits."""

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_bytes: int = DEFAULT_MAX_BYTES,
        concurrency: int = DEFAULT_CONCURRENCY,
        user_agent: str = _DEFAULT_UA,
    ) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.concurrency = max(1, concurrency)
        self.user_agent = user_agent

    # -- async -------------------------------------------------------------

    async def _download_one(self, client, url: str) -> DownloadedMedia:
        digest = hashlib.sha256()
        buf = bytearray()
        total = 0
        async with client.stream("GET", url, timeout=self.timeout) as resp:
            resp.raise_for_status()
            header_ct = resp.headers.get("content-type", "")
            async for chunk in resp.aiter_bytes():
                total += len(chunk)
                if total > self.max_bytes:
                    raise MediaDownloadError(
                        f"{url!r} exceeds max_bytes cap ({self.max_bytes})"
                    )
                digest.update(chunk)
                buf.extend(chunk)
        data = bytes(buf)
        content_type = resolve_content_type(header_ct, data)
        if content_type is None:
            raise MediaDownloadError(f"{url!r} is not a supported image type")
        return DownloadedMedia(
            url=url, data=data, content_type=content_type, sha256=digest.hexdigest()
        )

    async def download_many_async(
        self, urls: Iterable[str]
    ) -> list[DownloadedMedia | None]:
        """Fetch many URLs concurrently. Dead links resolve to ``None``."""

        try:  # lazy, optional dependency
            import httpx  # type: ignore
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError("httpx is not installed. Run: pip install httpx") from exc

        urls = list(urls)
        sem = asyncio.Semaphore(self.concurrency)
        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(
            follow_redirects=True, headers=headers
        ) as client:

            async def _guarded(u: str) -> DownloadedMedia | None:
                async with sem:
                    try:
                        return await self._download_one(client, u)
                    except Exception:  # noqa: BLE001
                        return None  # graceful: skip dead/blocked candidate

            return await asyncio.gather(*(_guarded(u) for u in urls))

    # -- sync --------------------------------------------------------------

    def fetch(self, url: str) -> DownloadedMedia | None:
        """Synchronously fetch a single asset; returns ``None`` on any failure."""

        try:
            import requests  # type: ignore
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError("requests is not installed.") from exc

        digest = hashlib.sha256()
        buf = bytearray()
        total = 0
        try:
            with requests.get(
                url,
                stream=True,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            ) as resp:
                resp.raise_for_status()
                header_ct = resp.headers.get("content-type", "")
                for chunk in resp.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > self.max_bytes:
                        return None
                    digest.update(chunk)
                    buf.extend(chunk)
        except Exception:  # noqa: BLE001
            return None

        data = bytes(buf)
        content_type = resolve_content_type(header_ct, data)
        if content_type is None:
            return None
        return DownloadedMedia(
            url=url, data=data, content_type=content_type, sha256=digest.hexdigest()
        )

    def fetch_many(self, urls: Iterable[str]) -> list[DownloadedMedia | None]:
        """Blocking wrapper that drives the async downloader via asyncio.run."""

        return asyncio.run(self.download_many_async(urls))


def default_downloader() -> MediaDownloader:
    """Build a downloader honouring the SEARCH_* environment defaults."""

    max_candidates = settings.search_max_candidates
    return MediaDownloader(concurrency=min(DEFAULT_CONCURRENCY, max(1, max_candidates)))


__all__ = [
    "ALLOWED_CONTENT_TYPES",
    "DownloadedMedia",
    "MediaDownloadError",
    "MediaDownloader",
    "default_downloader",
    "normalize_content_type",
    "resolve_content_type",
    "sha256_hex",
    "sniff_image_type",
    "validate_content_type",
]
