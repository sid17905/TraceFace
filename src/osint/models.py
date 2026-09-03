"""TraceFace — OSINT data models and shared primitives (Member 2).

This module defines the canonical data contracts for the OSINT engine. The
serialized form of :class:`OSINTSearchOutput` matches the ``OSINTSearchOutput``
schema in ``docs/COMMON_REFERENCE.md`` §1.2 key-for-key, so the payload can be
consumed directly by Member 3's cryptographic packaging stage.

Everything here is pure standard library so the package imports (and the unit
tests run) without any third-party dependency installed.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Optional, Sequence

# ---------------------------------------------------------------------------
# Error codes  (docs/COMMON_REFERENCE.md §3)
# ---------------------------------------------------------------------------


class OSINTErrorCode(IntEnum):
    """Standard exit / error codes owned by the OSINT stage."""

    ERR_OSINT_NO_MATCH = 201       # Web search returned 0 candidate visual matches
    ERR_SIMILARITY_REJECT = 202    # Candidates found but every similarity < threshold


class OSINTError(RuntimeError):
    """Raised for recoverable OSINT failures, carrying a standard error code."""

    def __init__(self, code: OSINTErrorCode, message: str = "") -> None:
        self.code = code
        self.message = message or code.name
        super().__init__(f"[{int(code)} {code.name}] {self.message}")


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SearchEngine(str):
    """String constants for the ``search_engine_used`` field."""

    GOOGLE_LENS_SERPAPI = "google_lens_serpapi"
    BING_VISUAL_SEARCH = "bing_visual_search"
    PLAYWRIGHT_FALLBACK = "playwright_fallback"
    NONE = "none"


# Canonical platform labels. Keys are lowercase identifiers used internally;
# values are the human-facing labels emitted in the schema.
PLATFORM_LABELS = {
    "twitter": "Twitter/X",
    "reddit": "Reddit",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "generic": "Web",
}

# Domains prioritized when ranking reverse-image candidates.
SOCIAL_DOMAINS = (
    "twitter.com",
    "x.com",
    "reddit.com",
    "redd.it",
    "instagram.com",
    "linkedin.com",
)


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------


def new_search_id() -> str:
    """Return a fresh URN-formatted UUID for a search run."""

    return f"urn:uuid:{uuid.uuid4()}"


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string with a ``Z`` suffix."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def cosine_similarity(u: Sequence[float], v: Sequence[float]) -> float:
    """Cosine similarity of two equal-length vectors.

    Member 1's ArcFace vectors are L2-normalized, so this reduces to a dot
    product for them, but we compute the full form for robustness. Returns
    ``0.0`` for mismatched lengths or zero-norm inputs rather than raising, so a
    single malformed candidate never crashes the verification loop.
    """

    if not u or not v or len(u) != len(v):
        return 0.0
    dot = 0.0
    nu = 0.0
    nv = 0.0
    for a, b in zip(u, v):
        dot += a * b
        nu += a * a
        nv += b * b
    if nu <= 0.0 or nv <= 0.0:
        return 0.0
    return dot / (math.sqrt(nu) * math.sqrt(nv))


# ---------------------------------------------------------------------------
# Intermediate models (internal pipeline state, not part of the wire schema)
# ---------------------------------------------------------------------------


@dataclass
class SearchCandidate:
    """A single visual-match candidate returned by a search engine."""

    source_url: str
    source_title: str = ""
    thumbnail_url: str = ""
    media_url: str = ""          # direct full-resolution media link, if known
    platform: str = "generic"    # internal key from PLATFORM_LABELS
    engine: str = SearchEngine.GOOGLE_LENS_SERPAPI

    def to_evidence(self) -> "SearchEvidence":
        return SearchEvidence(
            source_title=self.source_title,
            source_url=self.source_url,
            thumbnail_url=self.thumbnail_url,
        )


@dataclass
class SocialPost:
    """Harvested metadata for a single social-media / web post."""

    platform: str                       # internal key from PLATFORM_LABELS
    post_url: str
    author_handle: str = ""
    author_display_name: str = ""
    post_text: str = ""
    published_timestamp: str = ""       # ISO-8601
    media_url: str = ""                 # direct full-resolution media link
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def platform_label(self) -> str:
        return PLATFORM_LABELS.get(self.platform, PLATFORM_LABELS["generic"])


# ---------------------------------------------------------------------------
# Wire models  (serialized form == docs/COMMON_REFERENCE.md §1.2)
# ---------------------------------------------------------------------------


@dataclass
class BiometricVerification:
    """Biometric cross-verification verdict for a candidate."""

    cosine_similarity: float
    is_authentic_match: bool
    threshold_enforced: float = 0.68

    def to_dict(self) -> dict[str, Any]:
        return {
            "cosine_similarity": round(float(self.cosine_similarity), 4),
            "is_authentic_match": bool(self.is_authentic_match),
            "threshold_enforced": float(self.threshold_enforced),
        }


@dataclass
class SearchEvidence:
    """A raw, unverified search hit retained for the audit trail."""

    source_title: str
    source_url: str
    thumbnail_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_title": self.source_title,
            "source_url": self.source_url,
            "thumbnail_url": self.thumbnail_url,
        }


@dataclass
class VerifiedMatch:
    """The single, biometrically-confirmed provenance match."""

    platform: str                       # human label, e.g. "Twitter/X"
    post_url: str
    author_handle: str
    author_display_name: str
    post_text: str
    published_timestamp: str
    target_media_url: str
    target_media_sha256: str
    biometric_verification: BiometricVerification

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "post_url": self.post_url,
            "author_handle": self.author_handle,
            "author_display_name": self.author_display_name,
            "post_text": self.post_text,
            "published_timestamp": self.published_timestamp,
            "target_media_url": self.target_media_url,
            "target_media_sha256": self.target_media_sha256,
            "biometric_verification": self.biometric_verification.to_dict(),
        }

    @classmethod
    def from_post(
        cls,
        post: SocialPost,
        target_media_url: str,
        target_media_sha256: str,
        verification: BiometricVerification,
    ) -> "VerifiedMatch":
        return cls(
            platform=post.platform_label,
            post_url=post.post_url,
            author_handle=post.author_handle,
            author_display_name=post.author_display_name,
            post_text=post.post_text,
            published_timestamp=post.published_timestamp,
            target_media_url=target_media_url or post.media_url,
            target_media_sha256=target_media_sha256,
            biometric_verification=verification,
        )


@dataclass
class OSINTSearchOutput:
    """Top-level OSINT result — serializes to the ``OSINTSearchOutput`` schema."""

    query_scan_id: str
    search_engine_used: str = SearchEngine.NONE
    execution_time_seconds: float = 0.0
    candidates_discovered: int = 0
    top_verified_match: Optional[VerifiedMatch] = None
    raw_search_evidence: list[SearchEvidence] = field(default_factory=list)
    search_id: str = field(default_factory=new_search_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "search_id": self.search_id,
            "query_scan_id": self.query_scan_id,
            "search_engine_used": self.search_engine_used,
            "execution_time_seconds": round(float(self.execution_time_seconds), 2),
            "candidates_discovered": int(self.candidates_discovered),
            "top_verified_match": (
                self.top_verified_match.to_dict() if self.top_verified_match else None
            ),
            "raw_search_evidence": [e.to_dict() for e in self.raw_search_evidence],
        }

    def to_json(self, indent: int | None = 2) -> str:
        import json

        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def has_verified_match(self) -> bool:
        return self.top_verified_match is not None


__all__ = [
    "OSINTErrorCode",
    "OSINTError",
    "SearchEngine",
    "PLATFORM_LABELS",
    "SOCIAL_DOMAINS",
    "new_search_id",
    "utc_now_iso",
    "cosine_similarity",
    "SearchCandidate",
    "SocialPost",
    "BiometricVerification",
    "SearchEvidence",
    "VerifiedMatch",
    "OSINTSearchOutput",
]
