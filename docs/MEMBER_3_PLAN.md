# ⛓️ Member 3 Execution Plan: Web3, Storage & Cryptographic Systems Engineer
**Role:** Web3 & Cryptography Lead  
**Focus:** Solidity Smart Contracts, IPFS Decentralized Storage, Merkle Proofs & Zero-Tamper Verification  
**Sprint Duration:** 3 Days (Hackathon Ready)  

---

## 1. Technological Maneuvers & High-Grade Innovations
1. **Gas-Optimized Provenance Smart Contract (`FaceProvenanceRegistry.sol`):**
   - Implements $O(1)$ constant-time lookup and verification mappings.
   - Anchors 32-byte cryptographic Merkle roots and IPFS CIDv1 strings without high-gas overhead.
   - Deploys to Polygon Amoy Testnet, Arbitrum Sepolia, or local Hardhat/Anvil EVM network.
2. **Deterministic Canonical JSON (RFC 8785):** Guarantees zero byte discrepancies across systems by enforcing canonical key ordering and standardized float/string encodings before hashing.
3. **Cryptographic Merkle Provenance Tree:** Combines four distinct forensic evidentiary components into a single root:
   $$\text{Merkle Root} = \text{Keccak256}\Big(\text{Keccak256}(\text{QueryImage}) \oplus \text{Keccak256}(\text{Embedding}) \oplus \text{Keccak256}(\text{SocialPost}) \oplus \text{Keccak256}(\text{TargetMedia})\Big)$$
4. **Dual IPFS Storage Layer:** Pins forensic payloads to IPFS via Pinata SDK / Web3.Storage with local content-addressed fallback caching.
5. **Bidirectional Zero-Tamper Verification Engine:**
   - Ingestion mode: Re-evaluates local files against on-chain state.
   - Cryptographic proof mode: Downloads artifact from IPFS, recalculates Merkle root, and compares with blockchain state.
   - Tamper Demonstration Mode (`--simulate-tamper`): Live on-screen simulation modifying 1 character in the post text to prove the cryptographic ledger immediately flags and rejects the altered data.

---

## 2. 3-Day Hour-by-Hour Roadmap

### Day 1: Smart Contract Design, Testing & EVM Deployment
* **09:00 - 11:00 (Hardhat Setup & Contract Skeleton):**
  - Setup Node.js Hardhat environment with OpenZeppelin contracts.
  - Configure `hardhat.config.js` for Localhost, Arbitrum Sepolia, and Polygon Amoy.
  - Setup test wallets and acquire testnet tokens.
* **11:00 - 14:00 (Solidity Contract Implementation):**
  - Write `contracts/FaceProvenanceRegistry.sol`:
    - Storage struct: `ProvenanceRecord(recordHash, ipfsCid, faceVectorHash, timestamp, registrant, isValid)`.
    - Functions: `registerProvenance(...)`, `verifyProvenance(...)`, `getRecordCount()`.
    - Events: `ProvenanceRegistered(bytes32 indexed recordHash, string ipfsCid, bytes32 indexed faceVectorHash, address indexed registrant, uint64 timestamp)`.
* **14:00 - 15:00:** Lunch & Team Sync 1 (Review ABI & contract interfaces in `COMMON_REFERENCE.md`).
* **15:00 - 18:00 (Contract Unit Tests & Deployment Scripts):**
  - Write Hardhat unit tests in `test/FaceProvenanceRegistry.test.js` (100% code coverage: double registration rejection, query non-existent record, valid registration verification).
  - Write `contracts/scripts/deploy.js`.
  - Deploy contract to Polygon Amoy / Arbitrum Sepolia and record deployed address.
* **18:00 - 20:00 (Deliverable Review):**
  - Export contract ABI and address to `src/blockchain/contract_abi.json`.

---

### Day 2: Cryptographic Engine, IPFS Integration & Web3 Bridge
* **09:00 - 12:00 (Canonical JSON & Merkle Tree Engine):**
  - Implement `src/crypto/canonicalizer.py`: RFC 8785 canonical JSON serializer.
  - Implement `src/crypto/merkle.py`: Keccak-256 Merkle tree calculation for forensic payloads.
  - Implement `src/crypto/hasher.py`: SHA-256 and Keccak-256 byte-stream utilities.
* **12:00 - 14:00 (IPFS Decentralized Storage Client):**
  - Implement `src/storage/ipfs_client.py`:
    - Uploads JSON artifact to Pinata / IPFS node.
    - Receives CIDv1 (`bafy...`).
    - Implements deterministic retrieval via IPFS public gateways.
* **14:00 - 15:00:** Lunch & Team Sync 2 (Wire Web3 module with Member 1 and Member 2 payloads).
* **15:00 - 18:00 (Python Web3 Provider & Transaction Signer):**
  - Implement `src/blockchain/client.py`:
    - Ingests Merkle Root, IPFS CID, and Face Vector Hash.
    - Builds transaction, estimates gas, signs with private key, and broadcasts to RPC.
    - Waits for transaction receipt and extracts block number, tx hash, and gas used.
* **18:00 - 20:00 (Unit Tests for Crypto & Storage):**
  - Write `tests/test_crypto.py` and `tests/test_contracts.py`.

---

### Day 3: Zero-Tamper Verifier, CLI Integration & Live Demo Prep
* **09:00 - 12:00 (Verification Engine):**
  - Implement `src/blockchain/verifier.py`:
    - Subcommand 1: Verify by Record Hash (`TraceFace verify --hash 0x...`).
    - Subcommand 2: Verify by Input Image (`TraceFace verify --image path/to/image.jpg`).
    - Fetches on-chain record, downloads IPFS payload, verifies Merkle root integrity, checks timestamp, and outputs green "AUTHENTIC" or red "TAMPERED".
  - Implement `--simulate-tamper` flag for live hackathon demonstration.
* **12:00 - 14:00 (Full Pipeline Wiring):**
  - Connect `src/blockchain/` into `src/pipeline/orchestrator.py`.
  - Format output with block explorer hyperlinks (Polygonscan / Arbiscan).
* **14:00 - 15:00:** Lunch & Team Sync 3 (Full dry run of demo video recording).
* **15:00 - 18:00 (Screen Recording Session):**
  - Assist in screen recording:
    - Step 1: Run scan -> show discovered post -> show IPFS CID generation -> show on-chain transaction confirmation on block explorer.
    - Step 2: Run verification CLI -> show green verification banner.
    - Step 3: Run verification CLI with tampered file -> show instant red alert catching the modification.
* **18:00 - 20:00 (Final Documentation & GitHub Push):**
  - Document Smart Contract address, RPC config, and verification instructions in `README.md`.

---

## 3. Key Deliverable Files
* `contracts/FaceProvenanceRegistry.sol`
* `contracts/scripts/deploy.js`
* `src/crypto/canonicalizer.py`
* `src/crypto/merkle.py`
* `src/crypto/hasher.py`
* `src/storage/ipfs_client.py`
* `src/blockchain/client.py`
* `src/blockchain/verifier.py`
* `tests/test_crypto.py`
* `tests/test_contracts.py`

---

## 4. Verification & Testing Checklist
- [ ] Contract deploys cleanly with zero compilation warnings.
- [ ] Contract unit tests pass 100% on Hardhat network.
- [ ] Transaction broadcast generates valid transaction hash verifiable on Block Explorer.
- [ ] IPFS payload is accessible via standard IPFS gateways.
- [ ] Verification command correctly confirms authentic records with matching hashes.
- [ ] Verification command detects and rejects tampered data when payload is altered.
