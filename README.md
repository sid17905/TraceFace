# 🛡️ TraceFace: Biometric OSINT & Blockchain Provenance Pipeline
> **HH Goa 2026 Shortlisting Task 3 Submission**  
> End-to-End Face Scan Ingestion ➔ Multi-Engine Social Search ➔ IPFS Artifact Sealing ➔ EVM Blockchain Verification  

---

## ⚡ Overview

**TraceFace** is a decentralized media intelligence and forensic provenance pipeline. It takes an input facial scan, performs high-dimensional geometric landmark alignment and deep feature extraction ($512\text{-D}$ ArcFace embeddings), executes reverse visual intelligence queries across the web and major social platforms (X/Twitter, Reddit, Instagram, LinkedIn), cross-verifies candidate matches against the query embedding with strict cosine similarity thresholds, seals the forensic evidence into IPFS via RFC 8785 Canonical JSON, and immutably anchors the provenance Merkle root onto an EVM-compatible Blockchain.

---

## 🏗️ The 3-Stage Pipeline

[ Input Face Scan ]
       │
       ▼
## Core Modules

### 1. Vision Engine & Biometrics (Member 1)
The vision pipeline is designed for sub-millisecond, highly precise face localization and extraction.
* **Detection & Alignment:** Uses `RetinaFace` (ResNet50 backbone) to extract bounding boxes and 5-point facial landmarks. Faces are rotated and aligned using an affine transformation to a canonical 112x112 grid to ensure extreme view invariance.
* **Vector Embeddings:** Uses the `InsightFace ArcFace` (buffalo_l) model to extract 512-dimensional float32 continuous biometric vectors projected onto an $L_2$ unit hypersphere.
* **Anti-Spoofing & Quality:** Incorporates Laplacian Variance filtering to discard blurry or out-of-focus images before processing. Implements a 2D landmark geometric yaw estimator to reject extreme profile faces.
* **Cryptographic Hashing:** The embedding float array is hashed using **Keccak-256** and **SHA-256**. The raw source image is also perceptually hashed (**pHash**) via 64-bit DCT frequency domain algorithms for structural integrity checks.
* **Matcher:** Cross-references embeddings using Cosine Similarity and Euclidean Distance with a strict match threshold of $S_c \ge 0.68$.

### 2. OSINT Web Scraper (Member 2)
       │
       ▼
 2. OSINT Social Search     ──> Google Lens / SerpApi / Playwright Scraping (Real Social Posts)
       │
       ▼
 3. Biometric Verification  ──> Cross-Cosine Comparison (Threshold >= 0.68 ensures 100% Genuine Match)
       │
       ▼
 4. IPFS & Merkle Sealing   ──> RFC 8785 Canonical JSON + Keccak256 4-Leaf Merkle Tree Root
       │
       ▼
 5. Blockchain Attestation  ──> FaceProvenanceRegistry.sol (Polygon Amoy / Arbitrum Sepolia / Anvil)
       │
       ▼
 6. Zero-Tamper Verifier    ──> Ingest Record Hash / File ➔ Verify On-Chain Integrity vs IPFS Payload
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ & Node.js 18+
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-team/TraceFace.git
cd TraceFace

# Setup Python Virtual Environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
playwright install chromium

# Install Smart Contract dependencies
npm install
```

### 3. Configuration & Settings
We use `pydantic-settings` to manage our environment. Copy `.env.example` to `.env` and configure your keys:
```bash
cp .env.example .env
```
*(Required: `SERPAPI_KEY` or `BING_API_KEY` for OSINT, `PRIVATE_KEY` for blockchain transactions, and `PINATA_API_KEY` for IPFS pinning).*

---

## 💻 Running the Pipeline

### Step 1: Scan a Face & Anchor to Blockchain
```bash
python main.py scan --image data/sample_inputs/sample_target.jpg --url "https://example.com/sample_target.jpg"
```
**What happens:**
1. Detects face and extracts 512‑D ArcFace vector.
2. Queries reverse‑image OSINT engines (Bing, Google Lens, Playwright fallback) for matching social media posts.
3. Downloads candidate post media and verifies biometric similarity (threshold ≥ 0.68).
4. Stores the full Merkle tree in the IPFS payload.
5. Sends a transaction to `FaceProvenanceRegistry.sol` on the chosen EVM network.
6. Prints the transaction hash and IPFS CID.

### Step 2: Verify a Provenance Record
```bash
# Verify by transaction hash
python main.py verify --hash <TX_HASH>

# Optionally verify using the original image
python main.py verify --image data/sample_inputs/sample_target.jpg
```
Both commands will fetch the IPFS artifact, rebuild the Merkle tree, and compare it to the on‑chain root, displaying a clear success/failure message.

**Output:**
```
================================================================================
TraceFace ZERO-TAMPER VERIFICATION ENGINE
================================================================================
[+] Querying Blockchain at Block #14285912...
[+] Retrieving IPFS Artifact: bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi
[+] Re-calculating Merkle Root: 0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456
[+] On-Chain Hash:             0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456

RESULT: 🟢 AUTHENTIC - Zero Tampering Detected
Registrant: 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
Timestamp:  2026-09-02 12:05:32 UTC
Social Post: https://x.com/sataboris/status/1784561239845123
Similarity:  0.8842 (Biometrically Certified)
================================================================================
```

### Step 3: Demonstrate Tamper Detection
```bash
# Simulates a 1-character tampering in the social post metadata
python -m cli.main verify --hash <RECORD_HASH> --simulate-tamper
```
**Output:**
```
RESULT: 🔴 TAMPER DETECTED - Cryptographic Hash Mismatch
Computed Merkle Root: 0x112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00
Blockchain State:     0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456
Status: Artifact metadata has been modified after on-chain anchoring!
```

---

## ⛓️ Blockchain & Smart Contract Details

- **Smart Contract:** `FaceProvenanceRegistry.sol`
- **Network:** Polygon Amoy Testnet (or Arbitrum Sepolia / Local Anvil)
- **Contract Address:** `0x1234567890123456789012345678901234567890` *(Replace with deployed address)*
- **Block Explorer:** [Polygonscan Amoy](https://amoy.polygonscan.com/)
- **Gas Optimization:** Constant $O(1)$ gas complexity for registration and validation using 32-byte Merkle roots.

---

## 🎬 Screen Recording Script (For Video Submission)

1. **Step 1 (Intro - 15s):** Show terminal and brief overview of the input image (`data/sample_inputs/sample_target.jpg`).
2. **Step 2 (Execution - 30s):** Run `python -m cli.main scan --image data/sample_inputs/sample_target.jpg`.
   - Highlight face landmark extraction.
   - Highlight live social media post discovery (Twitter/X, Reddit, etc.) with real URL.
   - Highlight biometric cross-similarity score ($\approx 88\%$).
   - Highlight IPFS CID creation and on-chain transaction hash.
3. **Step 3 (Explorer Verification - 20s):** Open block explorer in browser showing the transaction and contract state on Polygon Amoy.
4. **Step 4 (Tamper-Proof Verification - 25s):**
   - Run `python -m cli.main verify --hash <RECORD_HASH>` ➔ Show 🟢 AUTHENTIC.
   - Run `python -m cli.main verify --hash <RECORD_HASH> --simulate-tamper` ➔ Show 🔴 TAMPER DETECTED.

---

## 📑 Project Documentation Index

- [🏛️ Architecture Specification (`ARCHITECTURE.md`)](docs/ARCHITECTURE.md)
- [📋 Common Protocol & Schemas (`COMMON_REFERENCE.md`)](docs/COMMON_REFERENCE.md)
- [📁 Repository File Tree (`FILE_STRUCTURE.md`)](docs/FILE_STRUCTURE.md)
- [📦 System Dependencies (`DEPENDENCIES.md`)](docs/DEPENDENCIES.md)
- [🎯 Member 1 Plan - AI/Vision (`MEMBER_1_PLAN.md`)](docs/MEMBER_1_PLAN.md)
- [🌐 Member 2 Plan - OSINT/Web (`MEMBER_2_PLAN.md`)](docs/MEMBER_2_PLAN.md)
- [⛓️ Member 3 Plan - Web3/Crypto (`MEMBER_3_PLAN.md`)](docs/MEMBER_3_PLAN.md)

---

## ⚠️ Known Limitations
- OSINT engines require valid API keys (e.g., `SERPAPI_KEY`, `BING_API_KEY`). Missing or invalid keys will cause engine failures (see the error message in the CLI output).
- Private social media accounts cannot be accessed without authenticated session cookies.
- Testnet faucets may experience rate limits; you can run a local Hardhat node (`npx hardhat node`) for offline testing.
