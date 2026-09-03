"""Multi-engine OSINT search dispatcher + biometric verification loop (Member 2).

This is the orchestration core of the OSINT stage. It:

1. Discovers candidate posts with a cascading strategy
   (Google Lens/SerpApi → Bing Visual Search → Playwright headless fallback).
2. For each candidate, harvests the social-post metadata, downloads the target
   media in-memory, and asks Member 1's biometric matcher for a cosine score.
3. Enforces the strict match gate (``cosine ≥ threshold``, default 0.68),
   stopping at the first authentic match.
4. Emits an :class:`~src.osint.models.OSINTSearchOutput` whose serialized form
   matches ``docs/COMMON_REFERENCE.md`` §1.2 exactly.

The matcher, downloader and search engines are all dependency-injectable, which
keeps the whole pipeline unit-testable offline with fakes. When no matcher or no
query embedding is supplied the dispatcher runs in *discovery-only* mode
(candidates are returned, but nothing is biometrically verified).
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

from .lens_search import BingVisualSearch, LensSearchEngine
from .media_downloader import MediaDownloader
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
)
from .playwright_scraper import PlaywrightScraper
from . import social_parsers

logger = logging.getLogger("traceface.osint")

# A matcher is any callable (query_embedding, candidate_image_bytes) -> cosine.
MatcherFn = Callable[[Sequence[float], bytes], float]

DEFAULT_THRESHOLD = 0.68


@dataclass
class OSINTQuery:
    """Input to a single OSINT search run."""

    query_scan_id: str
    image_url: Optional[str] = None            # public URL for API engines
    image_path: Optional[str] = None           # local file for Playwright fallback
    query_embedding: Optional[Sequence[float]] = None  # Member 1 ArcFace vector
    max_candidates: int = 10
    similarity_threshold: Optional[float] = None


def _as_matcher_fn(matcher: Any) -> Optional[MatcherFn]:
    """Adapt a variety of matcher shapes into a ``(embedding, bytes) -> float``.

    Accepts a plain callable, or a Member-1 matcher object exposing one of the
    common method names below. Returns ``None`` when no matcher is provided.
    """

    if matcher is None:
        return None
    # Prefer an explicit, well-known method on a Member-1 matcher object.
    for name in ("compare_image", "score_image", "similarity_from_image", "verify_image"):
        method = getattr(matcher, name, None)
        if callable(method):
            return lambda emb, data, _m=method: float(_m(emb, data))
    # Otherwise treat it as a plain callable (function / lambda / callable object).
    if callable(matcher):
        return lambda emb, data, _m=matcher: float(_m(emb, data))
    raise TypeError(
        "matcher must be callable (embedding, image_bytes) -> float, or expose "
        "one of: compare_image / score_image / similarity_from_image / verify_image"
    )


class OSINTDispatcher:
    """Cascading reverse-visual search manager with a biometric rejection gate."""

    def __init__(
        self,
        matcher: Any = None,
        *,
        lens: Optional[LensSearchEngine] = None,
        bing: Optional[BingVisualSearch] = None,
        playwright: Optional[PlaywrightScraper] = None,
        downloader: Optional[MediaDownloader] = None,
        threshold: Optional[float] = None,
    ) -> None:
        self.matcher_fn = _as_matcher_fn(matcher)
        self.lens = lens if lens is not None else LensSearchEngine()
        self.bing = bing if bing is not None else BingVisualSearch()
        self.playwright = playwright if playwright is not None else PlaywrightScraper()
        self.downloader = downloader if downloader is not None else MediaDownloader()
        if threshold is not None:
            self.threshold = threshold
        else:
            try:
                self.threshold = float(
                    os.getenv("FACE_SIMILARITY_THRESHOLD", str(DEFAULT_THRESHOLD))
                )
            except ValueError:
                self.threshold = DEFAULT_THRESHOLD

    # -- stage 1: discovery ------------------------------------------------

    def discover(self, query: OSINTQuery) -> tuple[list[SearchCandidate], str]:
        """Run the cascading search strategy; return (candidates, engine_label)."""

        # Primary: Google Lens via SerpApi.
        if query.image_url and self.lens.is_configured:
            try:
                found = self.lens.search(
                    image_url=query.image_url, max_candidates=query.max_candidates
                )
                if found:
                    return found, SearchEngine.GOOGLE_LENS_SERPAPI
            except Exception as exc:  # engine failure must not abort the cascade
                logger.warning("Lens search failed: %s", exc)

        # Secondary: Bing Visual Search.
        if query.image_url and self.bing.is_configured:
            try:
                found = self.bing.search(
                    query.image_url, max_candidates=query.max_candidates
                )
                if found:
                    return found, SearchEngine.BING_VISUAL_SEARCH
            except Exception as exc:
                logger.warning("Bing search failed: %s", exc)

        # Autonomous fallback: Playwright headless browser on a local image.
        if query.image_path:
            try:
                found = self.playwright.reverse_image_search(
                    query.image_path, max_candidates=query.max_candidates
                )
                if found:
                    return found, SearchEngine.PLAYWRIGHT_FALLBACK
            except Exception as exc:
                logger.warning("Playwright fallback failed: %s", exc)

        return [], SearchEngine.NONE

    # -- stage 2: candidate resolution + verification ----------------------

    def _resolve_post(self, candidate: SearchCandidate) -> SocialPost:
        """Harvest post metadata, synthesizing a minimal record on parser failure."""

        try:
            post = social_parsers.parse_post(candidate.source_url)
        except Exception as exc:
            logger.debug("Parser error for %s: %s", candidate.source_url, exc)
            post = None
        if post is None:
            post = SocialPost(
                platform=candidate.platform,
                post_url=candidate.source_url,
                post_text=candidate.source_title,
                media_url=candidate.media_url,
            )
        if not post.media_url:
            post.media_url = candidate.media_url
        return post

    def verify_candidates(
        self, candidates: list[SearchCandidate], query: OSINTQuery
    ) -> tuple[Optional[VerifiedMatch], list[SearchEvidence]]:
        """Download + biometrically score candidates; stop at first authentic hit."""

        evidence = [c.to_evidence() for c in candidates]
        threshold = (
            query.similarity_threshold
            if query.similarity_threshold is not None
            else self.threshold
        )

        # Discovery-only mode: no matcher or no query vector to compare against.
        if self.matcher_fn is None or not query.query_embedding:
            logger.info("Discovery-only mode: skipping biometric verification.")
            return None, evidence

        for candidate in candidates:
            post = self._resolve_post(candidate)
            media_url = post.media_url or candidate.media_url
            if not media_url:
                continue
            media = self.downloader.fetch(media_url)
            if media is None:
                logger.debug("Skipping dead/invalid media: %s", media_url)
                continue
            try:
                score = float(self.matcher_fn(query.query_embedding, media.data))
            except Exception as exc:
                logger.debug("Matcher error on %s: %s", media_url, exc)
                continue
            logger.info("Candidate %s scored cosine=%.4f", post.post_url, score)
            if score >= threshold:
                verification = BiometricVerification(
                    cosine_similarity=score,
                    is_authentic_match=True,
                    threshold_enforced=threshold,
                )
                match = VerifiedMatch.from_post(
                    post,
                    target_media_url=media.url,
                    target_media_sha256=media.sha256,
                    verification=verification,
                )
                return match, evidence

        return None, evidence

    # -- top-level entry ---------------------------------------------------

    def search(self, query: OSINTQuery, strict: bool = False) -> OSINTSearchOutput:
        """Execute the full OSINT stage and return an ``OSINTSearchOutput``.

        With ``strict=True`` the dispatcher raises :class:`OSINTError` when no
        candidate is discovered (201) or none pass the biometric gate (202),
        matching the standard error codes in ``COMMON_REFERENCE.md`` §3.
        """

        started = time.perf_counter()
        candidates, engine = self.discover(query)
        candidates = candidates[: max(0, query.max_candidates)]

        if strict and not candidates:
            raise OSINTError(
                OSINTErrorCode.ERR_OSINT_NO_MATCH,
                "Reverse image search returned no candidate visual matches.",
            )

        top_match, evidence = self.verify_candidates(candidates, query)
        elapsed = time.perf_counter() - started

        if strict and self.matcher_fn is not None and query.query_embedding and top_match is None and candidates:
            raise OSINTError(
                OSINTErrorCode.ERR_SIMILARITY_REJECT,
                "Candidates found but none met the biometric similarity threshold.",
            )

        return OSINTSearchOutput(
            query_scan_id=query.query_scan_id,
            search_engine_used=engine,
            execution_time_seconds=elapsed,
            candidates_discovered=len(candidates),
            top_verified_match=top_match,
            raw_search_evidence=evidence,
        )


def run_osint_search(
    query_scan_id: str,
    *,
    image_url: Optional[str] = None,
    image_path: Optional[str] = None,
    query_embedding: Optional[Sequence[float]] = None,
    matcher: Any = None,
    max_candidates: int = 10,
    threshold: Optional[float] = None,
    strict: bool = False,
) -> OSINTSearchOutput:
    """Convenience entry point for the pipeline orchestrator.

    Wires a query and dispatcher together in one call. Pass Member 1's matcher
    and the query's ArcFace embedding to enable biometric verification.
    """

    query = OSINTQuery(
        query_scan_id=query_scan_id,
        image_url=image_url,
        image_path=image_path,
        query_embedding=query_embedding,
        max_candidates=max_candidates,
        similarity_threshold=threshold,
    )
    dispatcher = OSINTDispatcher(matcher=matcher, threshold=threshold)
    return dispatcher.search(query, strict=strict)


__all__ = [
    "OSINTQuery",
    "OSINTDispatcher",
    "MatcherFn",
    "run_osint_search",
]
