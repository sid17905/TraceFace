# 📋 Common Reference & Protocol Specifications
**Project:** TraceFace OSINT & Blockchain Provenance Pipeline  
**Target:** HH Goa 2026 Shortlisting Task 3  
**Status:** Canonical Inter-Member Protocol Specification  

---

## 1. Unified Pipeline Data Schemas

All modules (Member 1, Member 2, Member 3) strictly adhere to the following data contracts using Pydantic / TypeScript Typed Interfaces.

### 1.1 Face Scan Result Schema (`FaceScanOutput`)
Output from **Member 1 (Vision Engine)** consumed by **Member 2** and **Member 3**.

```json
{
  "scan_id": "urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "timestamp_utc": "2026-09-02T12:00:00.000Z",
  "source_image_path": "data/inputs/target_person.jpg",
  "image_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "quality_metrics": {
    "laplacian_blur_score": 342.15,
    "is_blurry": false,
    "confidence_score": 0.9984
  },
  "bounding_box": {
    "x_min": 140,
    "y_min": 85,
    "x_max": 380,
    "y_max": 410,
    "landmarks_5pt": [
      [205, 180], [315, 182], [260, 240], [215, 310], [305, 312]
    ]
  },
  "embedding_vector": [0.0345, -0.1284, "... 512 float values ..."],
  "embedding_hash_keccak256": "0x4a5d8b79e6f302b1c8e9f2a4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3",
  "perceptual_hash_phash": "d3f28a9c1e74b065"
}
```

---

### 1.2 Social Media Search Result Schema (`OSINTSearchOutput`)
Output from **Member 2 (OSINT Engine)** combining search findings with verification scores.

```json
{
  "search_id": "urn:uuid:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "query_scan_id": "urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "search_engine_used": "google_lens_serpapi",
  "execution_time_seconds": 2.45,
  "candidates_discovered": 8,
  "top_verified_match": {
    "platform": "Twitter/X",
    "post_url": "https://x.com/sataboris/status/1784561239845123",
    "author_handle": "@sataboris",
    "author_display_name": "Boris Sata",
    "post_text": "Presenting our latest work at the AI Summit in Goa! #Hackathon2026",
    "published_timestamp": "2026-04-18T10:30:00Z",
    "target_media_url": "https://pbs.twimg.com/media/GJ8v0xXbkAA5aYl.jpg",
    "target_media_sha256": "9f83c6042a98f12b6a94...3984",
    "biometric_verification": {
      "cosine_similarity": 0.8842,
      "is_authentic_match": true,
      "threshold_enforced": 0.68
    }
  },
  "raw_search_evidence": [
    {
      "source_title": "AI Summit Highlights - Boris Sata",
      "source_url": "https://x.com/sataboris/status/1784561239845123",
      "thumbnail_url": "https://encrypted-tbn0.gstatic.com/images?q=..."
    }
  ]
}
```

---

### 1.3 Cryptographic Provenance Payload (IPFS DAG Schema)
Canonical JSON packed by **Member 3 (Blockchain & Storage Engine)** before hashing and IPFS pinning.

```json
{
  "version": "1.0.0-TraceFace",
  "canonical_standard": "RFC-8785",
  "created_at_utc": "2026-09-02T12:00:05.123Z",
  "biometric_evidence": {
    "source_image_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "embedding_hash_keccak256": "0x4a5d8b79e6f302b1c8e9f2a4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3",
    "cosine_similarity": 0.8842
  },
  "social_provenance": {
    "platform": "Twitter/X",
    "post_url": "https://x.com/sataboris/status/1784561239845123",
    "author_handle": "@sataboris",
    "post_text_sha256": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    "media_asset_url": "https://pbs.twimg.com/media/GJ8v0xXbkAA5aYl.jpg",
    "media_asset_sha256": "9f83c6042a98f12b6a94...3984",
    "published_timestamp": "2026-04-18T10:30:00Z"
  },
  "cryptographic_merkle": {
    "leaf_source_image": "0x...",
    "leaf_face_embedding": "0x...",
    "leaf_social_post": "0x...",
    "leaf_target_media": "0x...",
    "merkle_root": "0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456"
  }
}
```

---

### 1.4 Smart Contract ABI & Interface (`IFaceProvenanceRegistry.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFaceProvenanceRegistry {
    struct ProvenanceRecord {
        bytes32 recordHash;         // Merkle Root of Provenance Payload
        string ipfsCid;             // IPFS Content Identifier (CIDv1)
        bytes32 faceVectorHash;     // Keccak256 of 512-D float embedding
        uint64 timestamp;           // Block timestamp of registration
        address registrant;         // Wallet address of pipeline node
        bool isValid;               // Verification state flag
    }

    event ProvenanceRegistered(
        bytes32 indexed recordHash,
        string ipfsCid,
        bytes32 indexed faceVectorHash,
        address indexed registrant,
        uint64 timestamp
    );

    function registerProvenance(
        bytes32 recordHash,
        string calldata ipfsCid,
        bytes32 faceVectorHash
    ) external returns (bool);

    function verifyProvenance(
        bytes32 recordHash
    ) external view returns (
        bool exists,
        string memory ipfsCid,
        bytes32 faceVectorHash,
        uint64 timestamp,
        address registrant
    );

    function getRecordCount() external view returns (uint256);
}
```

---

## 2. Shared Environment Variables (`.env.example`)

Every team member will have a `.env` in the root directory:

```bash
# ==========================================
# TraceFace SYSTEM ENVIRONMENT CONFIGURATION
# ==========================================

# Member 1: AI / CV Configuration
FACE_DETECTION_CONFIDENCE=0.85
FACE_SIMILARITY_THRESHOLD=0.68
EMBEDDING_MODEL_BACKBONE=buffalo_l
DEVICE=cpu # 'cuda' or 'cpu'

# Member 2: OSINT & Web Search API Keys
SERPAPI_KEY=your_serpapi_key_here
BING_VISUAL_SEARCH_KEY=your_bing_visual_key_optional
PLAYWRIGHT_HEADLESS=true
SEARCH_MAX_CANDIDATES=10

# Member 3: Web3 & Storage Configuration
# Default: Polygon Amoy Testnet / Arbitrum Sepolia / Local Anvil
RPC_URL=https://rpc-amoy.polygon.technology/
CHAIN_ID=80002
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
PINATA_API_KEY=your_pinata_api_key_here
PINATA_SECRET_KEY=your_pinata_secret_key_here
IPFS_GATEWAY=https://gateway.pinata.cloud/ipfs/

# Global CLI Settings
LOG_LEVEL=INFO
ENABLE_RICH_TERMINAL=true
```

---

## 3. Standard Exit & Error Codes

| Error Code | Identifier | Description | Recovery Strategy |
|---|---|---|---|
| `ERR_NO_FACE_DETECTED` | 101 | No valid human face found in query image | Prompt user for higher quality / better lit image |
| `ERR_MULTIPLE_FACES` | 102 | Multiple faces found in image with ambiguous focus | Isolate primary bounding box or ask user to crop |
| `ERR_IMAGE_BLURRY` | 103 | Laplacian blur score below minimum threshold | Request non-blurred input image |
| `ERR_OSINT_NO_MATCH` | 201 | Web search returned 0 candidate visual matches | Fallback to secondary search provider or manual URL scan |
| `ERR_SIMILARITY_REJECT` | 202 | Candidate matches discovered but similarity < 0.68 | Continue searching deeper candidates or report no authentic match |
| `ERR_IPFS_UPLOAD_FAIL` | 301 | IPFS node timeout / Pinata API failure | Fallback to local Kubo node or retry with exponential backoff |
| `ERR_RPC_BROADCAST_FAIL`| 302 | Gas estimation error / RPC node timeout | Retry with 1.2x gas bump or switch fallback RPC |
| `ERR_TAMPER_DETECTED` | 401 | Verification failed: Computed hash != Ledger hash | Immediate CLI red alert: Data has been altered |
