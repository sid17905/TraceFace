"""Offline unit tests for the OSINT engine (Member 2).

Runs under both ``python -m unittest`` and ``pytest`` with **no network access
and no third-party packages installed** — every engine, downloader and parser
is exercised either through its pure functions or through dependency-injected
fakes. The repo root is inserted on ``sys.path`` so ``import src.osint`` resolves
regardless of the working directory the runner is launched from.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

# --- make ``src`` importable no matter where the runner is invoked from ----
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES = REPO_ROOT / "data" / "fixtures"

from src.osint import (
    BiometricVerification,
    DownloadedMedia,
    OSINTDispatcher,
    OSINTError,
    OSINTErrorCode,
    OSINTQuery,
    OSINTSearchOutput,
    SearchCandidate,
    SearchEngine,
    SocialPost,
    VerifiedMatch,
    cosine_similarity,
    detect_platform,
    new_search_id,
    parse_serpapi_response,
    prioritize_social,
    run_osint_search,
    sha256_hex,
)
from src.osint import dispatcher as dispatcher_mod
from src.osint import media_downloader as md
from src.osint import playwright_scraper as pw
from src.osint.lens_search import (
    BingVisualSearch,
    LensSearchEngine,
    parse_bing_response,
)
from src.osint.social_parsers import (
    generic_web,
    instagram,
    reddit,
    twitter,
)

# ===========================================================================
# models
# ===========================================================================


class TestCosineSimilarity(unittest.TestCase):
    def test_identical_unit_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)

    def test_orthogonal(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_opposite(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)

    def test_mismatched_lengths_return_zero(self):
        self.assertEqual(cosine_similarity([1.0, 0.0], [1.0]), 0.0)

    def test_empty_returns_zero(self):
        self.assertEqual(cosine_similarity([], []), 0.0)

    def test_zero_norm_returns_zero(self):
        self.assertEqual(cosine_similarity([0.0, 0.0], [1.0, 1.0]), 0.0)


class TestModelHelpers(unittest.TestCase):
    def test_new_search_id_is_urn(self):
        sid = new_search_id()
        self.assertTrue(sid.startswith("urn:uuid:"))
        self.assertEqual(len(sid.split(":")[-1].split("-")), 5)

    def test_candidate_to_evidence(self):
        c = SearchCandidate(
            source_url="https://x.com/a/status/1",
            source_title="t",
            thumbnail_url="th",
        )
        ev = c.to_evidence()
        self.assertEqual(ev.source_url, "https://x.com/a/status/1")
        self.assertEqual(ev.source_title, "t")
        self.assertEqual(ev.thumbnail_url, "th")

    def test_social_post_platform_label(self):
        self.assertEqual(SocialPost("twitter", "u").platform_label, "Twitter/X")
        self.assertEqual(SocialPost("reddit", "u").platform_label, "Reddit")
        self.assertEqual(SocialPost("unknown", "u").platform_label, "Web")

    def test_biometric_verification_rounds(self):
        d = BiometricVerification(0.876543, True, 0.68).to_dict()
        self.assertEqual(d["cosine_similarity"], 0.8765)
        self.assertIs(d["is_authentic_match"], True)
        self.assertEqual(d["threshold_enforced"], 0.68)


class TestVerifiedMatch(unittest.TestCase):
    def test_from_post_uses_human_label_and_fields(self):
        post = SocialPost(
            platform="twitter",
            post_url="https://twitter.com/janedoe/status/1",
            author_handle="@janedoe",
            author_display_name="Jane Doe",
            post_text="hello",
            published_timestamp="2024-01-01T00:00:00Z",
            media_url="https://pbs.twimg.com/media/x.jpg",
        )
        verification = BiometricVerification(0.9, True, 0.68)
        m = VerifiedMatch.from_post(
            post,
            target_media_url="https://pbs.twimg.com/media/x.jpg",
            target_media_sha256="deadbeef",
            verification=verification,
        )
        self.assertEqual(m.platform, "Twitter/X")  # human label, not internal key
        self.assertEqual(m.author_handle, "@janedoe")
        self.assertEqual(m.target_media_sha256, "deadbeef")
        d = m.to_dict()
        self.assertEqual(d["biometric_verification"]["cosine_similarity"], 0.9)

    def test_from_post_falls_back_to_post_media_url(self):
        post = SocialPost(platform="reddit", post_url="u", media_url="fallback.jpg")
        m = VerifiedMatch.from_post(post, "", "sha", BiometricVerification(0.7, True))
        self.assertEqual(m.target_media_url, "fallback.jpg")


class TestOSINTSearchOutputSchema(unittest.TestCase):
    """The serialized form must match COMMON_REFERENCE.md §1.2 key-for-key."""

    EXPECTED_TOP_KEYS = {
        "search_id",
        "query_scan_id",
        "search_engine_used",
        "execution_time_seconds",
        "candidates_discovered",
        "top_verified_match",
        "raw_search_evidence",
    }
    EXPECTED_MATCH_KEYS = {
        "platform",
        "post_url",
        "author_handle",
        "author_display_name",
        "post_text",
        "published_timestamp",
        "target_media_url",
        "target_media_sha256",
        "biometric_verification",
    }
    EXPECTED_VERIF_KEYS = {
        "cosine_similarity",
        "is_authentic_match",
        "threshold_enforced",
    }
    EXPECTED_EVIDENCE_KEYS = {"source_title", "source_url", "thumbnail_url"}

    def test_empty_output_shape(self):
        out = OSINTSearchOutput(query_scan_id="scan-1")
        d = out.to_dict()
        self.assertEqual(set(d.keys()), self.EXPECTED_TOP_KEYS)
        self.assertIsNone(d["top_verified_match"])
        self.assertEqual(d["raw_search_evidence"], [])
        self.assertEqual(d["search_engine_used"], SearchEngine.NONE)
        self.assertFalse(out.has_verified_match)

    def test_full_output_shape_and_types(self):
        post = SocialPost(
            platform="twitter",
            post_url="https://twitter.com/a/status/1",
            author_handle="@a",
            author_display_name="A",
            post_text="txt",
            published_timestamp="2024-01-01T00:00:00Z",
            media_url="https://m/x.jpg",
        )
        match = VerifiedMatch.from_post(
            post, "https://m/x.jpg", "abc123", BiometricVerification(0.71, True, 0.68)
        )
        out = OSINTSearchOutput(
            query_scan_id="scan-9",
            search_engine_used=SearchEngine.GOOGLE_LENS_SERPAPI,
            execution_time_seconds=1.23456,
            candidates_discovered=3,
            top_verified_match=match,
            raw_search_evidence=[
                SearchCandidate("https://news/1", "n", "th").to_evidence()
            ],
        )
        d = out.to_dict()
        self.assertEqual(set(d.keys()), self.EXPECTED_TOP_KEYS)
        self.assertEqual(d["execution_time_seconds"], 1.23)  # rounded to 2dp
        self.assertEqual(d["candidates_discovered"], 3)
        self.assertEqual(set(d["top_verified_match"].keys()), self.EXPECTED_MATCH_KEYS)
        self.assertEqual(
            set(d["top_verified_match"]["biometric_verification"].keys()),
            self.EXPECTED_VERIF_KEYS,
        )
        self.assertEqual(
            set(d["raw_search_evidence"][0].keys()), self.EXPECTED_EVIDENCE_KEYS
        )
        self.assertTrue(out.has_verified_match)

    def test_to_json_roundtrips(self):
        out = OSINTSearchOutput(query_scan_id="scan-json")
        parsed = json.loads(out.to_json())
        self.assertEqual(parsed["query_scan_id"], "scan-json")


class TestOSINTError(unittest.TestCase):
    def test_carries_code_and_message(self):
        err = OSINTError(OSINTErrorCode.ERR_OSINT_NO_MATCH, "nothing found")
        self.assertEqual(err.code, 201)
        self.assertEqual(err.message, "nothing found")
        self.assertIn("201", str(err))

    def test_error_codes_values(self):
        self.assertEqual(int(OSINTErrorCode.ERR_OSINT_NO_MATCH), 201)
        self.assertEqual(int(OSINTErrorCode.ERR_SIMILARITY_REJECT), 202)


# ===========================================================================
# lens_search
# ===========================================================================


class TestLensParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(
            (FIXTURES / "mock_lens_response.json").read_text(encoding="utf-8")
        )

    def test_parse_skips_linkless_and_counts(self):
        candidates = parse_serpapi_response(self.fixture, max_candidates=10)
        # 5 entries in fixture, one has an empty link -> 4 candidates
        self.assertEqual(len(candidates), 4)

    def test_social_prioritized_first(self):
        candidates = parse_serpapi_response(self.fixture, max_candidates=10)
        platforms = [c.platform for c in candidates]
        # twitter + instagram (social) must precede the two generic hits
        self.assertEqual(platforms[:2], ["twitter", "instagram"])
        self.assertEqual(platforms[2:], ["generic", "generic"])

    def test_media_url_string_and_dict_forms(self):
        candidates = parse_serpapi_response(self.fixture, max_candidates=10)
        by_platform = {c.platform: c for c in candidates}
        self.assertEqual(
            by_platform["twitter"].media_url, "https://pbs.twimg.com/media/full2.jpg"
        )
        news = next(c for c in candidates if "news.example.com" in c.source_url)
        self.assertEqual(news.media_url, "https://news.example.com/img/full1.jpg")

    def test_max_candidates_truncation(self):
        candidates = parse_serpapi_response(self.fixture, max_candidates=2)
        self.assertEqual(len(candidates), 2)
        self.assertEqual([c.platform for c in candidates], ["twitter", "instagram"])

    def test_engine_tag(self):
        candidates = parse_serpapi_response(self.fixture)
        self.assertTrue(
            all(c.engine == SearchEngine.GOOGLE_LENS_SERPAPI for c in candidates)
        )


class TestPrioritizeSocialStable(unittest.TestCase):
    def test_stable_within_groups(self):
        cands = [
            SearchCandidate("https://news.a/1"),
            SearchCandidate("https://twitter.com/x/status/1"),
            SearchCandidate("https://news.b/2"),
            SearchCandidate("https://reddit.com/r/x/comments/1/y"),
        ]
        ordered = prioritize_social(cands)
        urls = [c.source_url for c in ordered]
        self.assertEqual(urls[0], "https://twitter.com/x/status/1")
        self.assertEqual(urls[1], "https://reddit.com/r/x/comments/1/y")
        # generic order preserved
        self.assertEqual(urls[2], "https://news.a/1")
        self.assertEqual(urls[3], "https://news.b/2")


class TestBingParsing(unittest.TestCase):
    def test_parse_bing_response(self):
        data = {
            "tags": [
                {
                    "actions": [
                        {
                            "data": {
                                "value": [
                                    {
                                        "hostPageUrl": "https://twitter.com/a/status/9",
                                        "name": "tweet",
                                        "thumbnailUrl": "https://th/9.jpg",
                                        "contentUrl": "https://c/9.jpg",
                                    },
                                    {
                                        "hostPageUrl": "https://news.site/z",
                                        "name": "news",
                                        "thumbnailUrl": "https://th/z.jpg",
                                        "contentUrl": "https://c/z.jpg",
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        candidates = parse_bing_response(data, max_candidates=10)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].platform, "twitter")  # social first
        self.assertEqual(candidates[0].engine, SearchEngine.BING_VISUAL_SEARCH)

    def test_parse_bing_empty(self):
        self.assertEqual(parse_bing_response({}, 10), [])


class TestEngineConfiguration(unittest.TestCase):
    def setUp(self):
        # Make configuration checks hermetic regardless of the runner's env.
        self._saved = {
            k: os.environ.pop(k, None)
            for k in ("SERPAPI_KEY", "BING_VISUAL_SEARCH_KEY")
        }

    def tearDown(self):
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v

    def test_lens_unconfigured_without_key(self):
        engine = LensSearchEngine(api_key="")
        self.assertFalse(engine.is_configured)

    def test_lens_search_requires_key(self):
        with self.assertRaises(RuntimeError):
            LensSearchEngine(api_key="").search(image_url="https://x/y.jpg")

    def test_lens_search_requires_image_url(self):
        with self.assertRaises(ValueError):
            LensSearchEngine(api_key="k").search(image_url=None)

    def test_bing_unconfigured_returns_empty(self):
        self.assertEqual(BingVisualSearch(api_key="").search("https://x/y.jpg"), [])


# ===========================================================================
# media_downloader
# ===========================================================================

# Minimal valid image byte-headers for magic-byte sniffing.
_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 8


class TestMediaHelpers(unittest.TestCase):
    def test_sha256_hex_known_value(self):
        self.assertEqual(
            sha256_hex(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_sniff_jpeg_png_webp(self):
        self.assertEqual(md.sniff_image_type(_JPEG), "image/jpeg")
        self.assertEqual(md.sniff_image_type(_PNG), "image/png")
        self.assertEqual(md.sniff_image_type(_WEBP), "image/webp")

    def test_sniff_unknown_and_short(self):
        self.assertIsNone(md.sniff_image_type(b"not-an-image-but-long-enough"))
        self.assertIsNone(md.sniff_image_type(b"\xff\xd8"))  # too short

    def test_normalize_content_type(self):
        self.assertEqual(md.normalize_content_type("image/JPEG; q=1"), "image/jpeg")
        self.assertEqual(md.normalize_content_type(""), "")

    def test_validate_content_type(self):
        self.assertTrue(md.validate_content_type("image/png"))
        self.assertFalse(md.validate_content_type("application/pdf"))

    def test_resolve_prefers_sniff_over_header(self):
        # Header lies (octet-stream) but bytes are PNG -> trust the bytes.
        self.assertEqual(
            md.resolve_content_type("application/octet-stream", _PNG), "image/png"
        )

    def test_resolve_falls_back_to_header(self):
        # Unsniffable bytes, but header is an allowed image type.
        blob = b"x" * 32
        self.assertEqual(md.resolve_content_type("image/jpeg", blob), "image/jpeg")

    def test_resolve_rejects_unknown(self):
        self.assertIsNone(md.resolve_content_type("text/html", b"x" * 32))


class TestDownloadedMedia(unittest.TestCase):
    def test_from_bytes_valid(self):
        m = DownloadedMedia.from_bytes("http://x/y.png", _PNG)
        self.assertEqual(m.content_type, "image/png")
        self.assertEqual(m.sha256, sha256_hex(_PNG))
        self.assertEqual(m.size, len(_PNG))

    def test_from_bytes_invalid_raises(self):
        with self.assertRaises(md.MediaDownloadError):
            DownloadedMedia.from_bytes("http://x/y", b"garbage" * 4)


# ===========================================================================
# social_parsers
# ===========================================================================


class TestDetectPlatform(unittest.TestCase):
    def test_all_platforms(self):
        self.assertEqual(detect_platform("https://twitter.com/a/status/1"), "twitter")
        self.assertEqual(detect_platform("https://x.com/a/status/1"), "twitter")
        self.assertEqual(detect_platform("https://www.reddit.com/r/x/1"), "reddit")
        self.assertEqual(detect_platform("https://redd.it/abcd"), "reddit")
        self.assertEqual(detect_platform("https://instagram.com/p/x/"), "instagram")
        self.assertEqual(detect_platform("https://linkedin.com/in/x"), "linkedin")
        self.assertEqual(detect_platform("https://example.com/x"), "generic")
        self.assertEqual(detect_platform(""), "generic")


class TestGenericWeb(unittest.TestCase):
    HTML = (
        '<html><head>'
        '<meta property="og:title" content="A Photo &amp; Story">'
        '<meta content="https://img.example/og.jpg" name="og:image">'  # reversed attr order
        '<meta property="og:url" content="https://canonical.example/post">'
        '<meta property="article:published_time" content="2024-05-01T10:00:00Z">'
        '<meta property="og:description" content="desc text">'
        '<script type="application/ld+json">'
        '{"@type":"Article","headline":"LD Headline","author":{"name":"Jane"}}'
        '</script>'
        '</head><body></body></html>'
    )

    def test_extract_open_graph_both_attr_orders(self):
        og = generic_web.extract_open_graph(self.HTML)
        self.assertEqual(og["og:title"], "A Photo & Story")  # entity unescaped
        self.assertEqual(og["og:image"], "https://img.example/og.jpg")
        self.assertEqual(og["og:url"], "https://canonical.example/post")

    def test_extract_json_ld(self):
        blocks = generic_web.extract_json_ld(self.HTML)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["headline"], "LD Headline")

    def test_parse_open_graph(self):
        post = generic_web.parse_open_graph(self.HTML, "https://fallback/url")
        self.assertEqual(post.post_url, "https://canonical.example/post")
        self.assertEqual(post.media_url, "https://img.example/og.jpg")
        self.assertEqual(post.published_timestamp, "2024-05-01T10:00:00Z")
        self.assertEqual(post.post_text, "A Photo & Story")

    def test_parse_open_graph_empty_html(self):
        post = generic_web.parse_open_graph("", "https://fallback/url")
        self.assertEqual(post.post_url, "https://fallback/url")


class TestInstagram(unittest.TestCase):
    def test_parse_title_handle(self):
        html = (
            '<meta property="og:title" content="Jane Doe (@janedoe) on Instagram">'
            '<meta property="og:image" content="https://scontent/x.jpg">'
            '<meta property="og:description" content="a nice caption">'
        )
        post = instagram.parse_instagram_html(html, "https://instagram.com/p/x/")
        self.assertEqual(post.platform, "instagram")
        self.assertEqual(post.author_display_name, "Jane Doe")
        self.assertEqual(post.author_handle, "@janedoe")
        self.assertEqual(post.post_text, "a nice caption")
        self.assertEqual(post.media_url, "https://scontent/x.jpg")


class TestTwitter(unittest.TestCase):
    def test_extract_tweet_id(self):
        self.assertEqual(
            twitter.extract_tweet_id("https://twitter.com/a/status/1699999999999999999"),
            "1699999999999999999",
        )
        self.assertEqual(
            twitter.extract_tweet_id("https://x.com/a/statuses/42"), "42"
        )
        self.assertIsNone(twitter.extract_tweet_id("https://twitter.com/a"))
        self.assertIsNone(twitter.extract_tweet_id(""))

    def test_syndication_token_deterministic(self):
        t1 = twitter.syndication_token("1699999999999999999")
        t2 = twitter.syndication_token("1699999999999999999")
        self.assertEqual(t1, t2)
        self.assertNotIn("0", t1)
        self.assertNotIn(".", t1)

    def test_syndication_url_contains_id_and_token(self):
        url = twitter.syndication_url("123")
        self.assertIn("id=123", url)
        self.assertIn("token=", url)

    def test_parse_syndication_json(self):
        data = {
            "id_str": "123",
            "text": "hello world",
            "created_at": "2024-01-01T00:00:00Z",
            "user": {"screen_name": "janedoe", "name": "Jane Doe", "verified": True},
            "mediaDetails": [{"media_url_https": "https://pbs.twimg.com/media/a.jpg"}],
        }
        post = twitter.parse_syndication_json(data, "https://twitter.com/janedoe/status/123")
        self.assertEqual(post.platform, "twitter")
        self.assertEqual(post.author_handle, "@janedoe")
        self.assertEqual(post.author_display_name, "Jane Doe")
        self.assertEqual(post.post_text, "hello world")
        self.assertEqual(post.media_url, "https://pbs.twimg.com/media/a.jpg")
        self.assertTrue(post.extra["verified"])


class TestReddit(unittest.TestCase):
    def test_to_json_url(self):
        self.assertEqual(
            reddit.to_json_url("https://www.reddit.com/r/x/comments/1/title/"),
            "https://www.reddit.com/r/x/comments/1/title.json",
        )
        self.assertEqual(
            reddit.to_json_url("https://www.reddit.com/r/x/comments/1/title?utm=1"),
            "https://www.reddit.com/r/x/comments/1/title.json",
        )
        self.assertEqual(
            reddit.to_json_url("https://www.reddit.com/r/x/1.json"),
            "https://www.reddit.com/r/x/1.json",
        )

    def test_parse_reddit_json(self):
        data = [
            {
                "data": {
                    "children": [
                        {
                            "kind": "t3",
                            "data": {
                                "author": "spez",
                                "title": "A title",
                                "selftext": "body text",
                                "permalink": "/r/x/comments/1/a_title/",
                                "created_utc": 1704067200,
                                "url_overridden_by_dest": "https://i.redd.it/abc.jpg",
                                "subreddit": "x",
                                "score": 42,
                                "num_comments": 7,
                            },
                        }
                    ]
                }
            }
        ]
        post = reddit.parse_reddit_json(data, "https://www.reddit.com/r/x/comments/1/")
        self.assertEqual(post.platform, "reddit")
        self.assertEqual(post.author_handle, "u/spez")
        self.assertEqual(post.media_url, "https://i.redd.it/abc.jpg")
        self.assertIn("A title", post.post_text)
        self.assertIn("body text", post.post_text)
        self.assertEqual(post.extra["subreddit"], "x")
        self.assertEqual(post.extra["score"], 42)
        self.assertTrue(post.published_timestamp.endswith("Z"))

    def test_parse_reddit_json_no_post(self):
        self.assertIsNone(reddit.parse_reddit_json([{"data": {"children": []}}], "u"))


# ===========================================================================
# playwright_scraper (pure helpers only)
# ===========================================================================


class TestPlaywrightPure(unittest.TestCase):
    def test_extract_links_dedupe_and_order(self):
        html = (
            '<a href="https://a.com/1">x</a>'
            '<a href="https://b.com/2">y</a>'
            "<a href='https://a.com/1'>dup</a>"
        )
        links = pw.extract_links(html)
        self.assertEqual(links, ["https://a.com/1", "https://b.com/2"])

    def test_links_to_candidates_drops_noise_and_sorts_social(self):
        links = [
            "https://www.google.com/search?q=x",  # noise -> dropped
            "https://news.site/story",  # generic
            "https://twitter.com/a/status/1",  # social
            "https://bing.com/images",  # noise -> dropped
        ]
        cands = pw.links_to_candidates(links)
        urls = [c.source_url for c in cands]
        self.assertEqual(len(cands), 2)
        self.assertEqual(urls[0], "https://twitter.com/a/status/1")  # social first
        self.assertEqual(urls[1], "https://news.site/story")
        self.assertTrue(
            all(c.engine == SearchEngine.PLAYWRIGHT_FALLBACK for c in cands)
        )

    def test_headless_env(self):
        prev = os.environ.get("PLAYWRIGHT_HEADLESS")
        try:
            os.environ["PLAYWRIGHT_HEADLESS"] = "false"
            self.assertFalse(pw._headless_from_env())
            os.environ["PLAYWRIGHT_HEADLESS"] = "true"
            self.assertTrue(pw._headless_from_env())
        finally:
            if prev is None:
                os.environ.pop("PLAYWRIGHT_HEADLESS", None)
            else:
                os.environ["PLAYWRIGHT_HEADLESS"] = prev


# ===========================================================================
# dispatcher  (integration, fully offline via injected fakes)
# ===========================================================================


class _FakeLens:
    """Stand-in for LensSearchEngine that never touches the network."""

    def __init__(self, candidates, configured=True):
        self._candidates = candidates
        self.is_configured = configured

    def search(self, image_url=None, image_path=None, max_candidates=10):
        return list(self._candidates)[:max_candidates]


class _UnconfiguredEngine:
    is_configured = False

    def search(self, *a, **k):  # pragma: no cover - should never be called
        raise AssertionError("unconfigured engine must not be searched")


class _FakeDownloader:
    """Returns deterministic in-memory media for known URLs, else None."""

    def __init__(self, table):
        # table: url -> bytes (or None for a dead link)
        self._table = table

    def fetch(self, url):
        data = self._table.get(url)
        if data is None:
            return None
        return DownloadedMedia(
            url=url, data=data, content_type="image/jpeg", sha256=sha256_hex(data)
        )


def _make_dispatcher(candidates, *, matcher=None, downloader=None, threshold=0.68):
    return OSINTDispatcher(
        matcher=matcher,
        lens=_FakeLens(candidates),
        bing=_UnconfiguredEngine(),
        playwright=_UnconfiguredEngine(),
        downloader=downloader if downloader is not None else _FakeDownloader({}),
        threshold=threshold,
    )


class TestMatcherAdapter(unittest.TestCase):
    def test_none(self):
        self.assertIsNone(dispatcher_mod._as_matcher_fn(None))

    def test_plain_callable(self):
        fn = dispatcher_mod._as_matcher_fn(lambda emb, data: 0.5)
        self.assertEqual(fn([1.0], b"x"), 0.5)

    def test_object_with_method(self):
        class M:
            def compare_image(self, emb, data):
                return 0.9

        fn = dispatcher_mod._as_matcher_fn(M())
        self.assertEqual(fn([1.0], b"x"), 0.9)

    def test_invalid_raises(self):
        with self.assertRaises(TypeError):
            dispatcher_mod._as_matcher_fn(object())


class TestDispatcherDiscoveryOnly(unittest.TestCase):
    def test_discovery_only_without_matcher(self):
        cands = [
            SearchCandidate("https://twitter.com/a/status/1", "t", "th1", platform="twitter"),
            SearchCandidate("https://news/2", "n", "th2"),
        ]
        disp = _make_dispatcher(cands)  # no matcher
        out = disp.search(OSINTQuery(query_scan_id="s1", image_url="https://q/f.jpg"))
        self.assertEqual(out.search_engine_used, SearchEngine.GOOGLE_LENS_SERPAPI)
        self.assertEqual(out.candidates_discovered, 2)
        self.assertIsNone(out.top_verified_match)
        self.assertEqual(len(out.raw_search_evidence), 2)

    def test_discovery_only_when_no_embedding(self):
        cands = [SearchCandidate("https://news/2", "n", "th2")]
        disp = _make_dispatcher(cands, matcher=lambda e, d: 0.99)
        # matcher present but query has no embedding -> discovery only
        out = disp.search(OSINTQuery(query_scan_id="s2", image_url="https://q/f.jpg"))
        self.assertIsNone(out.top_verified_match)

    def test_no_candidates_engine_none(self):
        disp = _make_dispatcher([])
        out = disp.search(OSINTQuery(query_scan_id="s3", image_url="https://q/f.jpg"))
        self.assertEqual(out.search_engine_used, SearchEngine.NONE)
        self.assertEqual(out.candidates_discovered, 0)


class TestDispatcherVerification(unittest.TestCase):
    def setUp(self):
        # Neutralize the network-dependent post resolver: pretend parsing failed
        # so the dispatcher synthesizes a post from the candidate itself.
        import src.osint.social_parsers as sp

        self._sp = sp
        self._orig_parse_post = sp.parse_post
        sp.parse_post = lambda url, timeout=15.0: None

    def tearDown(self):
        self._sp.parse_post = self._orig_parse_post

    def test_first_match_above_threshold_wins(self):
        cands = [
            SearchCandidate(
                "https://twitter.com/a/status/1",
                "low",
                "th1",
                media_url="https://m/low.jpg",
                platform="twitter",
            ),
            SearchCandidate(
                "https://twitter.com/b/status/2",
                "high",
                "th2",
                media_url="https://m/high.jpg",
                platform="twitter",
            ),
        ]
        downloader = _FakeDownloader(
            {"https://m/low.jpg": b"LOWDATA", "https://m/high.jpg": b"HIGHDATA"}
        )
        # score by payload: low fails, high passes
        scores = {b"LOWDATA": 0.40, b"HIGHDATA": 0.83}
        disp = _make_dispatcher(
            cands, matcher=lambda emb, data: scores[data], downloader=downloader
        )
        out = disp.search(
            OSINTQuery(
                query_scan_id="s4",
                image_url="https://q/f.jpg",
                query_embedding=[0.1, 0.2, 0.3],
            )
        )
        self.assertIsNotNone(out.top_verified_match)
        m = out.top_verified_match
        self.assertEqual(m.post_url, "https://twitter.com/b/status/2")
        self.assertEqual(m.target_media_sha256, sha256_hex(b"HIGHDATA"))
        self.assertTrue(m.biometric_verification.is_authentic_match)
        self.assertAlmostEqual(m.biometric_verification.cosine_similarity, 0.83)
        self.assertEqual(m.platform, "Twitter/X")

    def test_threshold_boundary_inclusive(self):
        cands = [
            SearchCandidate(
                "https://x.com/a/status/1", media_url="https://m/exact.jpg", platform="twitter"
            )
        ]
        downloader = _FakeDownloader({"https://m/exact.jpg": b"EXACT"})
        disp = _make_dispatcher(
            cands, matcher=lambda e, d: 0.68, downloader=downloader, threshold=0.68
        )
        out = disp.search(
            OSINTQuery(query_scan_id="s5", image_url="https://q/f.jpg", query_embedding=[1.0])
        )
        self.assertIsNotNone(out.top_verified_match)  # >= threshold passes

    def test_all_below_threshold_no_match(self):
        cands = [
            SearchCandidate(
                "https://x.com/a/status/1", media_url="https://m/a.jpg", platform="twitter"
            )
        ]
        downloader = _FakeDownloader({"https://m/a.jpg": b"AAA"})
        disp = _make_dispatcher(
            cands, matcher=lambda e, d: 0.50, downloader=downloader, threshold=0.68
        )
        out = disp.search(
            OSINTQuery(query_scan_id="s6", image_url="https://q/f.jpg", query_embedding=[1.0])
        )
        self.assertIsNone(out.top_verified_match)
        self.assertEqual(out.candidates_discovered, 1)  # still reported as discovered

    def test_dead_media_is_skipped(self):
        cands = [
            SearchCandidate(
                "https://x.com/a/status/1", media_url="https://m/dead.jpg", platform="twitter"
            ),
            SearchCandidate(
                "https://x.com/b/status/2", media_url="https://m/live.jpg", platform="twitter"
            ),
        ]
        downloader = _FakeDownloader(
            {"https://m/dead.jpg": None, "https://m/live.jpg": b"LIVE"}
        )
        disp = _make_dispatcher(
            cands, matcher=lambda e, d: 0.90, downloader=downloader
        )
        out = disp.search(
            OSINTQuery(query_scan_id="s7", image_url="https://q/f.jpg", query_embedding=[1.0])
        )
        self.assertIsNotNone(out.top_verified_match)
        self.assertEqual(out.top_verified_match.post_url, "https://x.com/b/status/2")


class TestDispatcherStrictMode(unittest.TestCase):
    def test_strict_raises_no_match_201(self):
        disp = _make_dispatcher([])
        with self.assertRaises(OSINTError) as ctx:
            disp.search(
                OSINTQuery(query_scan_id="s8", image_url="https://q/f.jpg"), strict=True
            )
        self.assertEqual(ctx.exception.code, OSINTErrorCode.ERR_OSINT_NO_MATCH)

    def test_strict_raises_similarity_reject_202(self):
        import src.osint.social_parsers as sp

        orig = sp.parse_post
        sp.parse_post = lambda url, timeout=15.0: None
        try:
            cands = [
                SearchCandidate(
                    "https://x.com/a/status/1",
                    media_url="https://m/a.jpg",
                    platform="twitter",
                )
            ]
            downloader = _FakeDownloader({"https://m/a.jpg": b"AAA"})
            disp = _make_dispatcher(
                cands, matcher=lambda e, d: 0.10, downloader=downloader
            )
            with self.assertRaises(OSINTError) as ctx:
                disp.search(
                    OSINTQuery(
                        query_scan_id="s9",
                        image_url="https://q/f.jpg",
                        query_embedding=[1.0],
                    ),
                    strict=True,
                )
            self.assertEqual(
                ctx.exception.code, OSINTErrorCode.ERR_SIMILARITY_REJECT
            )
        finally:
            sp.parse_post = orig


class TestRunOsintSearchOffline(unittest.TestCase):
    """run_osint_search builds real engines; with no API keys it degrades to none."""

    def setUp(self):
        self._saved = {
            k: os.environ.get(k)
            for k in ("SERPAPI_KEY", "BING_VISUAL_SEARCH_KEY", "FACE_SIMILARITY_THRESHOLD")
        }
        os.environ.pop("SERPAPI_KEY", None)
        os.environ.pop("BING_VISUAL_SEARCH_KEY", None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_no_keys_no_local_image_returns_none_engine(self):
        out = run_osint_search(query_scan_id="run-1", image_url="https://q/f.jpg")
        self.assertIsInstance(out, OSINTSearchOutput)
        self.assertEqual(out.search_engine_used, SearchEngine.NONE)
        self.assertEqual(out.candidates_discovered, 0)
        # schema still intact
        self.assertEqual(out.to_dict()["query_scan_id"], "run-1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
