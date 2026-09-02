# 🌐 Member 2 Execution Plan: OSINT & Web Search Systems Engineer
**Role:** OSINT & Web Intelligence Lead  
**Focus:** Reverse Visual Search Dispatcher, Social Media Scrapers, Metadata Harvesters & Media Pipeline  
**Sprint Duration:** 3 Days (Hackathon Ready)  

---

## 1. Technological Maneuvers & High-Grade Innovations
1. **Multi-Engine Reverse Visual Dispatcher:** Implements a cascading search strategy:
   - Primary: Google Lens API via SerpApi (unmatched accuracy across social networks).
   - Secondary: Bing Visual Search API.
   - Autonomous Fallback: Playwright Headless Browser cluster with stealth user-agent rotation and anti-bot evasions.
2. **Deep Social Media Parsers:** Custom parsers for Twitter/X, Reddit, Instagram, and LinkedIn that extract:
   - Canonical Post URL & Status ID
   - Author Handle, Display Name & Verified Status
   - ISO-8601 Post Timestamp
   - Text Caption & Hashtags
   - High-Resolution Media CDN Image URL
3. **Structured Open Graph & JSON-LD Parser:** Automatic extraction of Schema.org metadata for news articles, blogs, and general web pages where social posts are embedded.
4. **Asynchronous Concurrent Media Pipeline:** Uses `httpx` async connection pooling with strict timeouts and memory buffer limits to download candidates without touching disk.
5. **Biometric Cross-Verification Interlock:** Directly pipes downloaded candidate images into Member 1's `matcher.py` in real-time, instantly discarding false positives until a certified match ($S_c \ge 0.68$) is confirmed.

---

## 2. 3-Day Hour-by-Hour Roadmap

### Day 1: Search Dispatcher & Google Lens Integration
* **09:00 - 11:00 (Environment & API Setup):**
  - Setup Python virtual environment with `google-search-results`, `playwright`, `beautifulsoup4`, `httpx`.
  - Run `playwright install chromium`.
  - Configure `SERPAPI_KEY` in `.env`.
* **11:00 - 14:00 (Google Lens Search Engine):**
  - Implement `src/osint/lens_search.py`:
    - Upload query image or send direct URL/base64 to Google Lens engine.
    - Extract `visual_matches` list (title, source URL, thumbnail, direct link).
    - Filter results prioritizing social media domains (`twitter.com`, `x.com`, `reddit.com`, `instagram.com`, `linkedin.com`).
* **14:00 - 15:00:** Lunch & Team Sync 1 (Verify data contract with Member 1's `FaceScanOutput`).
* **15:00 - 18:00 (Async Media Downloader):**
  - Implement `src/osint/media_downloader.py`:
    - Async fetching of candidate high-res images.
    - SHA-256 calculation of image byte stream in-flight.
    - Content-type validation (JPEG, PNG, WebP).
* **18:00 - 20:00 (Unit Tests & Mocks):**
  - Write `tests/test_osint.py` with mock search fixtures (`data/fixtures/mock_lens_response.json`).
  - Deliverable: Working search function that takes an image and returns 5+ candidate URLs.

---

### Day 2: Social Media Parsers & Playwright Fallback
* **09:00 - 12:00 (Social Media Platform Parsers):**
  - Implement `src/osint/social_parsers/twitter.py`: Scrapes X/Twitter syndication API and DOM to extract author, timestamp, tweet text, and image URLs.
  - Implement `src/osint/social_parsers/reddit.py`: Uses Reddit JSON API (`/comments/{id}.json`) to extract post author, subreddit, score, timestamp, and full-resolution media.
  - Implement `src/osint/social_parsers/generic_web.py`: BeautifulSoup parser for OpenGraph (`og:image`, `og:title`, `article:published_time`).
* **12:00 - 14:00 (Playwright Autonomous Browser Fallback):**
  - Implement `src/osint/playwright_scraper.py`:
    - Launches headless Chromium instance.
    - Automates reverse visual search on public search portals.
    - Extracts candidate links directly from the rendered DOM.
* **14:00 - 15:00:** Lunch & Team Sync 2 (Wire Search Engine with Member 1's ArcFace matcher).
* **15:00 - 18:00 (Biometric Filtering Loop):**
  - Implement the verification loop in `src/osint/dispatcher.py`:
    - Loop over discovered candidates.
    - Download image -> Send to Member 1 `matcher.py` -> If $S_c \ge 0.68$, designate as `top_verified_match` and break loop.
* **18:00 - 20:00 (Output Packaging):**
  - Format output strictly to `OSINTSearchOutput` schema defined in `COMMON_REFERENCE.md`.

---

### Day 3: Pipeline Integration, Stress Testing & Demo Recording
* **09:00 - 12:00 (Pipeline Orchestration):**
  - Connect `src/osint/` to `src/pipeline/orchestrator.py`.
  - Ensure search results are handed off cleanly to Member 3's Merkle tree & IPFS publisher.
* **12:00 - 14:00 (Dynamic Test Targets):**
  - Test search pipeline with 5 diverse real-world images from Twitter, Reddit, and LinkedIn.
  - Verify that authentic posts are discovered genuinely in real-time without hardcoding.
* **14:00 - 15:00:** Lunch & Team Sync 3 (Demo recording rehearsal).
* **15:00 - 18:00 (Screen Recording Session):**
  - Screen-record the live execution of `TraceFace scan` demonstrating real-time social search queries, candidate evaluation logs, and discovered post URLs.
* **18:00 - 20:00 (Documentation & Edge Case Polish):**
  - Document OSINT scraping mechanisms and anti-bot mitigation in `README.md`.
  - Format and lint all code.

---

## 3. Key Deliverable Files
* `src/osint/dispatcher.py`
* `src/osint/lens_search.py`
* `src/osint/playwright_scraper.py`
* `src/osint/media_downloader.py`
* `src/osint/social_parsers/twitter.py`
* `src/osint/social_parsers/reddit.py`
* `src/osint/social_parsers/generic_web.py`
* `tests/test_osint.py`

---

## 4. Verification & Testing Checklist
- [ ] Reverse image search returns real social media candidate posts from a genuine query.
- [ ] Social parsers accurately extract author handle, timestamp, and high-res image URL.
- [ ] Async media downloader enforces timeouts and handles dead links gracefully.
- [ ] Search engine automatically filters out false matches using Member 1's biometric cosine score.
- [ ] Output payload matches `OSINTSearchOutput` schema 100%.
- [ ] Unit tests pass via `pytest tests/test_osint.py`.
