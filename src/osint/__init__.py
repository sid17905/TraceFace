"""TraceFace OSINT engine — public API (Member 2).

This package owns the *OSINT & web-search* stage of the TraceFace provenance
pipeline. Given a face crop (as a public URL and/or a local file) plus the
query's ArcFace embedding, it performs a cascading reverse-visual search,
harvests social-media provenance for each candidate, downloads the media
in-memory, and runs Member 1's biometric matcher to confirm a single authentic
match — emitting an :class:`OSINTSearchOutput` that serializes key-for-key to
the shared ``OSINTSearchOutput`` schema (``docs/COMMON_REFERENCE.md`` §1.2).

Typical use from the pipeline orchestrator::

    from src.osint import run_osint_search

    result = run_osint_search(
        query_scan_id=scan_id,
        image_url=hosted_face_url,          # for the API engines
        image_path=local_face_crop_path,    # for the Playwright fallback
        query_embedding=arcface_vector,     # from Member 1
        matcher=member1_matcher,            # (embedding, image_bytes) -> cosine
    )
    payload = result.to_dict()              # hand to Member 3

Without a ``matcher``/``query_embedding`` the engine runs in *discovery-only*
mode: it returns ranked candidates and raw evidence but performs no biometric
verification (``top_verified_match`` stays ``None``).
"""

from __future__ import annotations

# -- error codes & core data models ---------------------------------------
from .models import (
    BiometricVerification,
    OSINTError,
    OSINTErrorCode,
    OSINTSearchOutput,
    SearchCandidate,
    SearchEngine,
    SearchEvidence,
    SocialPost,
    VerifiedMatch,
    cosine_similarity,
    new_search_id,
    utc_now_iso,
    PLATFORM_LABELS,
    SOCIAL_DOMAINS,
)

# -- search engines --------------------------------------------------------
from .lens_search import (
    BingVisualSearch,
    LensSearchEngine,
    parse_bing_response,
    parse_serpapi_response,
    prioritize_social,
)
from .playwright_scraper import PlaywrightScraper

# -- media acquisition -----------------------------------------------------
from .media_downloader import (
    DownloadedMedia,
    MediaDownloader,
    MediaDownloadError,
    default_downloader,
    sha256_hex,
)

# -- social-media provenance parsers --------------------------------------
from .social_parsers import detect_platform, parse_post

# -- orchestration (the primary entry points) ------------------------------
from .dispatcher import (
    OSINTDispatcher,
    OSINTQuery,
    run_osint_search,
)

__version__ = "1.0.0"

__all__ = [
    # orchestration
    "OSINTDispatcher",
    "OSINTQuery",
    "run_osint_search",
    # models & contracts
    "OSINTSearchOutput",
    "VerifiedMatch",
    "BiometricVerification",
    "SearchCandidate",
    "SearchEvidence",
    "SocialPost",
    "SearchEngine",
    "PLATFORM_LABELS",
    "SOCIAL_DOMAINS",
    # errors
    "OSINTError",
    "OSINTErrorCode",
    # engines
    "LensSearchEngine",
    "BingVisualSearch",
    "PlaywrightScraper",
    "parse_serpapi_response",
    "parse_bing_response",
    "prioritize_social",
    # media
    "MediaDownloader",
    "DownloadedMedia",
    "MediaDownloadError",
    "default_downloader",
    "sha256_hex",
    # social parsers
    "detect_platform",
    "parse_post",
    # utilities
    "cosine_similarity",
    "new_search_id",
    "utc_now_iso",
    "__version__",
]
