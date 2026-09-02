# 📁 Repository File Structure & Module Ownership
**Project:** TraceFace OSINT & Blockchain Provenance Pipeline  
**Target:** HH Goa 2026 Shortlisting Task 3  

---

## 1. Directory Tree & Module Breakdown

```
TraceFace/
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # Multi-OS automated linting, test suite & contract tests
│
├── contracts/                         # [Member 3: Web3 & Cryptography]
│   ├── FaceProvenanceRegistry.sol     # Core EVM Smart Contract (Gas-optimized, tamper-evident)
│   ├── interfaces/
│   │   └── IFaceProvenanceRegistry.sol# Smart contract interface definition
│   └── scripts/
│       ├── deploy.js                  # Deployment script (Hardhat / Foundry / Ethers.js)
│       └── verify_contract.js         # Block explorer contract verification (Etherscan/Polygonscan)
│
├── src/                               # Core Pipeline Source Code
│   ├── __init__.py
│   │
│   ├── vision/                        # [Member 1: AI / Computer Vision Engine]
│   │   ├── __init__.py
│   │   ├── detector.py                # RetinaFace detector & 5-point landmark alignment
│   │   ├── embedder.py                # ArcFace / InsightFace 512-D vector extraction
│   │   ├── quality.py                 # Laplacian blur, illumination & resolution validation
│   │   └── matcher.py                 # Cosine similarity calculation & threshold evaluation
│   │
│   ├── osint/                         # [Member 2: OSINT Web & Social Search Engine]
│   │   ├── __init__.py
│   │   ├── dispatcher.py              # Multi-engine search manager (SerpApi / Lens / Bing)
│   │   ├── lens_search.py             # Google Lens API integration via SerpApi
│   │   ├── playwright_scraper.py      # Headless browser fallback for dynamic web & social scraping
│   │   ├── social_parsers/            # Platform-specific DOM and API parsers
│   │   │   ├── __init__.py
│   │   │   ├── twitter.py             # X/Twitter post, author, timestamp & image parser
│   │   │   ├── reddit.py              # Reddit submission parser
│   │   │   ├── instagram.py           # Instagram public post parser
│   │   │   └── generic_web.py         # Open Graph & JSON-LD metadata extractor
│   │   └── media_downloader.py        # Asynchronous media stream fetching with hash checks
│   │
│   ├── crypto/                        # [Member 3: Web3 & Cryptography]
│   │   ├── __init__.py
│   │   ├── canonicalizer.py           # RFC 8785 JSON Canonicalization Scheme (JCS)
│   │   ├── merkle.py                  # Cryptographic Merkle tree generator (Keccak-256)
│   │   └── hasher.py                  # SHA-256 / Keccak256 / Perceptual Hash utilities
│   │
│   ├── storage/                       # [Member 3: Web3 & Cryptography]
│   │   ├── __init__.py
│   │   ├── ipfs_client.py             # Pinata SDK / Web3.Storage / Local IPFS node gateway
│   │   └── local_cache.py             # Local SQLite / filesystem cache for rapid re-runs
│   │
│   ├── blockchain/                    # [Member 3: Web3 & Cryptography]
│   │   ├── __init__.py
│   │   ├── client.py                  # Web3.py / Ethers.js EVM JSON-RPC provider wrapper
│   │   └── verifier.py                # On-chain state query & cryptographic proof validation
│   │
│   └── pipeline/                      # [Integrated Pipeline Coordinator - All Members]
│       ├── __init__.py
│       ├── orchestrator.py            # End-to-end execution flow coordinator
│       └── types.py                   # Pydantic models & Type annotations for all stages
│
├── cli/                               # [Member 1 + Member 2: CLI & Terminal Experience]
│   ├── __init__.py
│   ├── main.py                        # Typer CLI entrypoint (`TraceFace scan`, `TraceFace verify`)
│   ├── ui.py                          # Rich console, biometric radars, tables, banners
│   └── demo_runner.py                 # 1-click deterministic automated demonstration script
│
├── tests/                             # Unified Test Suite
│   ├── test_vision.py                 # Member 1 unit tests (landmarks, embeddings, similarity)
│   ├── test_osint.py                  # Member 2 unit tests (search dispatcher, parsers, mocks)
│   ├── test_crypto.py                 # Member 3 unit tests (Merkle tree, canonical JSON, hashing)
│   ├── test_contracts.py              # Member 3 Hardhat / Anvil smart contract tests
│   └── test_e2e.py                    # End-to-end integration test
│
├── data/                              # Sample Data & Verification Artifacts
│   ├── sample_inputs/                 # Test images for demo video
│   │   ├── sample_satya_nadella.jpg
│   │   ├── sample_sam_altman.jpg
│   │   └── sample_vitalik_buterin.jpg
│   └── fixtures/                      # Mocked search responses for offline CI testing
│
├── .env.example                       # Shared environment variables template
├── .gitignore                         # Git ignore rules (node_modules, .venv, keys)
├── hardhat.config.js                  # Solidity compiler & network deployment configuration
├── package.json                       # Hardhat & web3 dependencies
├── requirements.txt                   # Python dependencies (InsightFace, OpenCV, Web3, Typer)
├── pyproject.toml                     # Python package metadata & linter configuration
├── ARCHITECTURE.md                    # System architecture & mathematical models
├── COMMON_REFERENCE.md                # Shared schemas, error codes & ABI definitions
├── FILE_STRUCTURE.md                  # This file
├── DEPENDENCIES.md                    # Comprehensive dependency & environment specification
├── MEMBER_1_PLAN.md                   # 3-Day execution plan for AI/CV Engineer
├── MEMBER_2_PLAN.md                   # 3-Day execution plan for OSINT/Web Engineer
├── MEMBER_3_PLAN.md                   # 3-Day execution plan for Web3/Blockchain Engineer
└── README.md                          # Main repository documentation & run guide
```

---

## 2. Module Ownership & Team Responsibilities

| Directory / Subsystem | Primary Owner | Secondary Reviewer | Core Deliverable |
|---|---|---|---|
| `src/vision/` | **Member 1 (AI/CV)** | Member 2 | Face detection, landmark alignment, 512-D ArcFace vectors, cosine similarity |
| `src/osint/` | **Member 2 (OSINT)** | Member 1 | Reverse visual search, social scrapers, metadata extractor, media downloader |
| `src/crypto/` & `contracts/` | **Member 3 (Web3)** | Member 1 | Merkle trees, canonical JSON, Solidity contracts, IPFS pinning, RPC interaction |
| `src/pipeline/` & `cli/` | **Joint (Lead: M1/M2)** | Member 3 | Unified CLI tool, orchestrated pipeline, live progress bars, demo script |
| `tests/` | **All Members** | All Members | 100% unit & integration test coverage for each domain |

---

## 3. Code Standards & Git Conventions

1. **Branching Strategy:**
   - `main`: Protected. Production-ready, passing all CI tests.
   - `feat/vision-engine` (Member 1)
   - `feat/osint-search` (Member 2)
   - `feat/blockchain-ipfs` (Member 3)
   - `feat/cli-integration` (Joint)

2. **Commit Message Format (Conventional Commits):**
   - `feat(vision): integrate insightface arcface 512d embeddings`
   - `feat(osint): add serpapi google lens parser with fallback`
   - `feat(contracts): add FaceProvenanceRegistry with merkle root anchoring`
   - `fix(crypto): canonicalize JSON key ordering per RFC 8785`
   - `docs: update submission checklist and demo video script`

3. **Type Safety & Linting:**
   - Strict Python type hints (`mypy --strict src/`)
   - `black` for formatting and `ruff` for linting.
   - Solidity: `solhint` and `prettier-plugin-solidity`.
