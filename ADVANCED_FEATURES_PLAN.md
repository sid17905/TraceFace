# 🛡️ TraceFace: Advanced Features Implementation Roadmap

> **CRITICAL DEVELOPER DIRECTIVES & CONSTRAINTS**  
> ⚠️ **STRICT GUARDRAILS:**
> 1. **DO NOT CHANGE PREVIOUS LOGIC OR UI:** Do not modify, break, or alter any previously implemented logic (RetinaFace/ArcFace pipeline, 2D-FFT frequency liveness in `src/vision/liveness.py`, canonical RFC 8785 Merkle tree, local IPFS cache, or existing Rich terminal panels) without asking the user and receiving explicit confirmation.
> 2. **ALL EXTERNAL API KEYS MUST BE OPTIONAL:** All API keys (`SERPAPI_KEY`, `BING_VISUAL_SEARCH_KEY`, `PINATA_API_KEY`, custom RPCs) must be **strictly optional** with robust local/deterministic fallbacks (e.g. offline mock data fixtures, local DAG builders, local IPFS caching, and simulated EVM nodes) so the pipeline runs smoothly out of the box with zero external dependencies.

---

## 📊 Feature Status Overview

| Feature | Scope / Module | Status | Core Responsibility |
|---|---|---|---|
| **Liveness & Synthetic Gating** | `src/vision/liveness.py` | ✅ **Already Implemented** | 2D-FFT Azimuthal Power Spectrum decay to reject GANs/Diffusion fakes. |
| **Feature 1: Temporal Origin & Propagation DAG** | `src/analytics/` & `cli/` | 🟡 **Pending Implementation** | Multi-hop timeline graph, Root-Zero detection, pHash degradation analysis. |
| **Feature 2: Decentralized Takedown & Ownership** | `contracts/` & `src/blockchain/` | 🟡 **Pending Implementation** | EIP-712 structured claim signing, Kleros dispute states (`REVOKED`/`DISPUTED`). |
| **Feature 3: Zero-Knowledge Biometric Proofs** | `circuits/` & `src/crypto/` | 🟡 **Pending Implementation** | Groth16 zk-SNARK proving Cosine Similarity $\ge 0.68$ without revealing 512-D vector. |

---

## 🌲 Feature 1: Temporal Origin & Propagation Graph (DAG Engine)

### 🎯 Objective
Reconstruct the cross-platform propagation timeline of an image across Twitter/X, Reddit, Instagram, and web portals to identify **"Root-Zero"** (the earliest authentic source) and track visual degradation across shares.

### 📐 Technical Architecture & Deliverables
1. **Pydantic Data Models (`src/pipeline/types.py` - append only, do not alter existing fields):**
   * `OriginNode`: `node_id`, `platform`, `post_url`, `author_handle`, `timestamp_utc`, `phash`, `similarity_score`, `laplacian_score`, `is_root_zero`.
   * `PropagationEdge`: `source_id`, `target_id`, `delta_seconds`, `phash_hamming_distance`, `degradation_score`.
   * `PropagationGraph`: `nodes: list[OriginNode]`, `edges: list[PropagationEdge]`, `root_zero_node_id: str`, `total_hops: int`.

2. **Graph Analytics Engine (`src/analytics/origin_graph.py`):**
   * Constructs a Directed Acyclic Graph (DAG) using timestamps and pHash proximity ($\text{Hamming Distance} \le 12$).
   * Resolves Root-Zero as the root node with in-degree $= 0$, earliest timestamp, and highest Laplacian sharpness.

3. **Degradation Analyzer (`src/analytics/degradation.py`):**
   * Calculates perceptual degradation and resolution decay between consecutive propagation nodes.

4. **Visualizer & CLI (`src/analytics/graph_visualizer.py` & `cli/ui.py`):**
   * Renders a Rich ASCII tree timeline waterfall:
     ```
     [Origin Root-Zero] 2026-04-18 10:30 UTC - Twitter/X (@creator)
            │
            ├─── (+4.2 hrs | pHash Δ=2) ──► Reddit (/r/technology)
            │
            └─── (+18.6 hrs | pHash Δ=6) ──► Instagram (@repost_hub)
     ```
   * Exports interactive Mermaid/SVG graph embedded inside the IPFS metadata artifact.

---

## ⚖️ Feature 2: Decentralized Takedown & Ownership Claims (EIP-712)

### 🎯 Objective
Enable creators and victims to cryptographically assert ownership over their biometric identity, submit non-repudiable takedown notices, and update on-chain provenance records to `DISPUTED` or `REVOKED`.

### 📐 Technical Architecture & Deliverables
1. **Smart Contract Extension (`contracts/FaceProvenanceRegistry.sol`):**
   * Add `enum RecordStatus { ACTIVE, DISPUTED, REVOKED, CONFIRMED }`.
   * Add `struct DisputeRecord { address claimant, uint8 reasonCode, string evidenceCid, uint256 timestamp, bool resolved }`.
   * Implement `submitTakedownClaim(bytes32 recordHash, uint8 reasonCode, string calldata evidenceCid, bytes calldata signature)`.
   * Implement `resolveDispute(bytes32 recordHash, RecordStatus newStatus)`.

2. **EIP-712 Typed Signing Module (`src/blockchain/eip712.py`):**
   * Encodes structured domain separator (`TraceFace Provenance Registry`, version `1`) and typed claims:
     ```json
     {
       "recordHash": "0x...",
       "claimant": "0x...",
       "reasonCode": 1,
       "evidenceIpfsCid": "bafybei...",
       "nonce": 0,
       "deadline": 1780000000
     }
     ```
   * Signs using `eth_account.messages.encode_typed_data`.

3. **Dispute Client & Verifier Integration (`src/blockchain/dispute_client.py` & `src/blockchain/verifier.py`):**
   * Connects takedown transactions to Web3 RPC.
   * `ZeroTamperVerifier` inspects dispute status and outputs appropriate status badges:
     * `🟢 AUTHENTIC`
     * `🟡 DISPUTED (Claim Filed)`
     * `⛔ REVOKED (Takedown Executed)`

---

## 🔐 Feature 3: Zero-Knowledge Biometric Proofs (zk-SNARKs)

### 🎯 Objective
Prove on-chain that **Query Embedding $u$** matches **Ledger Face Vector $v$** ($\text{Cosine Similarity} \ge 0.68$) without exposing either 512-dimensional float array to the blockchain or IPFS.

### 📐 Technical Architecture & Deliverables
1. **Embedding Quantizer (`src/crypto/quantizer.py`):**
   * Scales continuous float32 vectors $v \in [-1, 1]^{512}$ to signed integers:
     $$\tilde{v}_i = \text{round}(v_i \cdot 10^4)$$
   * Scaled threshold: $\tau = 0.68 \cdot 10^8 = 68{,}000{,}000$.

2. **Circom Circuit (`circuits/biometric_match.circom`):**
   * Validates Poseidon commitments: $\text{Poseidon}(\tilde{u}) = C_u$, $\text{Poseidon}(\tilde{v}) = C_v$.
   * Computes dot product $\sum_{i=1}^{512} \tilde{u}_i \cdot \tilde{v}_i \ge 68{,}000{,}000$.
   * Emits public output signal `isValidMatch = 1`.

3. **ZK Prover & Verifier (`src/crypto/zk_prover.py` & `contracts/ZkBiometricVerifier.sol`):**
   * Python wrapper for witness generation and Groth16 proof creation via `snarkjs`.
   * On-chain pairing verifier contract integrated with `FaceProvenanceRegistry.sol`.

---

## 🛠️ Step-by-Step Execution Sequence

```
STEP 1: Temporal Origin Graph (Analytics & Visualization)
├── 1.1 Append Origin & Graph models in src/pipeline/types.py
├── 1.2 Implement src/analytics/origin_graph.py & src/analytics/degradation.py
├── 1.3 Add Rich ASCII DAG timeline renderer in src/analytics/graph_visualizer.py
└── 1.4 Write unit tests in tests/test_origin_graph.py

STEP 2: Decentralized Takedown & Claims (EIP-712 & Contracts)
├── 2.1 Update contracts/interfaces/IFaceProvenanceRegistry.sol
├── 2.2 Extend contracts/FaceProvenanceRegistry.sol with dispute states
├── 2.3 Implement src/blockchain/eip712.py & src/blockchain/dispute_client.py
├── 2.4 Update src/blockchain/verifier.py with status checks
└── 2.5 Write unit tests in test/FaceProvenanceRegistry.test.js & tests/test_dispute.py

STEP 3: Zero-Knowledge Biometric Proofs (zk-SNARKs)
├── 3.1 Implement src/crypto/quantizer.py
├── 3.2 Create circuits/biometric_match.circom
├── 3.3 Implement src/crypto/zk_prover.py
├── 3.4 Deploy contracts/ZkBiometricVerifier.sol
└── 3.5 Write unit tests in tests/test_zk_snark.py

STEP 4: Unified CLI Integration
├── 4.1 Implement subcommands in cli/main.py (scan, verify, graph, takedown, zk-verify)
├── 4.2 Polish cli/ui.py visual components (ASCII trees, radar, status banners)
└── 4.3 Create cli/demo_runner.py for automated 1-click hackathon walkthrough
```
