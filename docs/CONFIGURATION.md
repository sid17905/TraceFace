# TraceFace Configuration Guide

Complete reference for all environment variables and system configuration.

## Table of Contents

- [Quick Start](#quick-start)
- [Member 1: Vision & AI Configuration](#member-1-vision--ai-configuration)
- [Member 2: OSINT Multi-Source Configuration](#member-2-osint-multi-source-configuration)
- [Member 3: Blockchain & IPFS Configuration](#member-3-blockchain--ipfs-configuration)
- [Global Settings](#global-settings)
- [Advanced Configuration](#advanced-configuration)

---

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure **required keys**:
   - `SERPAPI_KEY` or `BING_VISUAL_SEARCH_KEY` (at least one for OSINT)
   - `PINATA_API_KEY` + `PINATA_SECRET_KEY` (IPFS storage)
   - `PRIVATE_KEY` + `CONTRACT_ADDRESS` (blockchain attestation)

3. Test configuration:
   ```bash
   python -m cli.main verify --help
   ```

---

## Member 1: Vision & AI Configuration

### FACE_DETECTION_CONFIDENCE
- **Type**: Float (0.0-1.0)
- **Default**: 0.85
- **Description**: Minimum confidence threshold for RetinaFace face detection
- **Impact**: 
  - Lower values (0.75-0.85): More permissive, detects partially occluded faces
  - Higher values (0.85-0.95): Stricter, only high-confidence detections
- **Recommendation**: Keep at 0.85 for production

### FACE_SIMILARITY_THRESHOLD
- **Type**: Float (0.0-1.0)
- **Default**: 0.68
- **Description**: Cosine similarity threshold for biometric match verification
- **Impact**: 
  - 0.65-0.70: Strict matching (recommended for forensics)
  - 0.70-0.80: Moderate matching (social media deduplication)
  - > 0.80: Very permissive (loose clustering)
- **Recommendation**: 0.68 ensures high-confidence authentic matches

### EMBEDDING_MODEL_BACKBONE
- **Type**: String
- **Default**: buffalo_l
- **Options**: `buffalo_l`, `buffalo_mf`, `buffalo_f`
- **Description**: InsightFace ArcFace model variant
- **Size**: buffalo_l (~150MB), buffalo_mf (~90MB), buffalo_f (~40MB)
- **Accuracy**: buffalo_l > buffalo_mf > buffalo_f
- **Recommendation**: buffalo_l for highest accuracy

### DEVICE
- **Type**: String
- **Default**: cpu
- **Options**: `cpu`, `cuda`
- **Description**: Inference device for deep learning models
- **Performance**: CUDA provides 3-5x speedup over CPU
- **Requirements**: NVIDIA GPU with CUDA 11.x+

---

## Member 2: OSINT Multi-Source Configuration

### SERPAPI_KEY
- **Type**: String
- **Required**: Yes (or BING_VISUAL_SEARCH_KEY)
- **Description**: API key for SerpApi Google Lens reverse image search
- **Get Key**: https://serpapi.com/
- **Pricing**: Free tier (100 searches/month), Paid plans available
- **Multi-Source**: When configured, aggregates results from Google Lens

### BING_VISUAL_SEARCH_KEY
- **Type**: String
- **Optional**: Yes
- **Description**: API key for Bing Visual Search
- **Get Key**: https://azure.microsoft.com/en-us/services/cognitive-services/bing-visual-search/
- **Multi-Source**: When configured alongside SERPAPI_KEY, enables true multi-source aggregation
- **Impact**: Doubles candidate discovery when both keys are configured

### PLAYWRIGHT_HEADLESS
- **Type**: Boolean
- **Default**: true
- **Description**: Run Playwright browser in headless mode
- **Production**: Must be `true`
- **Debugging**: Set to `false` to see browser automation in real-time

### SEARCH_MAX_CANDIDATES
- **Type**: Integer
- **Default**: 10
- **Description**: Maximum candidates to extract from all OSINT sources combined
- **Impact**: 
  - Lower (5-10): Faster, focuses on top results
  - Higher (20-30): More comprehensive, slower processing
- **Recommendation**: 10-15 for optimal balance

---

## Member 3: Blockchain & IPFS Configuration

### RPC_URL
- **Type**: String (URL)
- **Required**: Yes
- **Description**: Ethereum JSON-RPC endpoint
- **Testnet Options**:
  - **Polygon Amoy**: `https://rpc-amoy.polygon.technology/`
  - **Arbitrum Sepolia**: `https://sepolia-rollup.arbitrum.io/rpc`
  - **Local Anvil**: `http://127.0.0.1:8545`
- **Production**: Use Alchemy, Infura, or QuickNode for reliability
- **Example**: `https://polygon-amoy.g.alchemy.com/v2/YOUR_KEY`

### CHAIN_ID
- **Type**: Integer
- **Default**: 80002 (Polygon Amoy)
- **Options**:
  - Polygon Amoy: 80002
  - Arbitrum Sepolia: 421614
  - Local Anvil: 31337
- **Description**: Chain ID for EIP-712 typed data signing
- **Must Match**: Must correspond to RPC_URL network

### PRIVATE_KEY
- **Type**: String (0x-prefixed hex)
- **Required**: Yes (for blockchain transactions)
- **Description**: Deployer wallet private key
- **Security**:
  - ⚠️ **NEVER commit to version control**
  - Use Anvil dev keys for testing (printed on startup)
  - Use Metamask test accounts for testnet
  - For production: Load from AWS Secrets Manager, HashiCorp Vault
- **Format**: `0x1234567890abcdef...` (64 hex characters)

### CONTRACT_ADDRESS
- **Type**: String (0x-prefixed address)
- **Required**: Yes
- **Description**: FaceProvenanceRegistry smart contract address
- **Deployment**: 
  ```bash
  npx hardhat run contracts/scripts/deploy.js --network amoy
  ```
- **Update**: After deployment, copy the printed address here

### PINATA_API_KEY + PINATA_SECRET_KEY
- **Type**: String
- **Required**: Yes (for IPFS storage)
- **Description**: Pinata API credentials for IPFS pinning
- **Get Keys**: https://www.pinata.cloud/
- **Pricing**: Free tier (1GB storage), Paid plans for more
- **Purpose**: Ensures forensic artifacts are permanently accessible

### IPFS_GATEWAY
- **Type**: String (URL)
- **Default**: https://gateway.pinata.cloud/ipfs/
- **Description**: IPFS content gateway for retrieval
- **Alternatives**:
  - `https://ipfs.io/ipfs/` (public, slower)
  - `https://cloudflare-ipfs.com/ipfs/` (fast CDN)
  - Custom IPFS node gateway
- **Recommendation**: Use Pinata gateway for pinned content

---

## Global Settings

### LOG_LEVEL
- **Type**: String
- **Default**: INFO
- **Options**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Description**: Application logging verbosity
- **Production**: INFO or WARNING
- **Development**: DEBUG

### ENABLE_RICH_TERMINAL
- **Type**: Boolean
- **Default**: true
- **Description**: Enable colored tables, progress bars, and rich UI
- **Production**: true
- **CI/CD**: Set to false if terminal doesn't support ANSI colors

---

## Advanced Configuration

### MAX_UPLOAD_BYTES
- **Type**: Integer
- **Default**: 15728640 (15 MB)
- **Description**: Maximum file upload size for API
- **Impact**: Adjust based on your server memory constraints

### DOWNLOAD_TIMEOUT_SECONDS
- **Type**: Integer
- **Default**: 15
- **Description**: Timeout for media downloads from social platforms
- **Recommendation**: 10-20 seconds

### DOWNLOAD_CONCURRENCY
- **Type**: Integer
- **Default**: 8
- **Description**: Maximum concurrent media downloads
- **Impact**: Higher values = faster processing, but more bandwidth
- **Recommendation**: 4-8 for most connections

### MAX_HAMMING_DISTANCE
- **Type**: Integer
- **Default**: 12
- **Description**: Perceptual hash Hamming distance threshold for origin DAG
- **Impact**:
  - 8-10: Stricter matching (same image transformations only)
  - 12-15: Moderate matching (cropped/compressed variants)
  - > 15: Permissive matching (similar but not identical)
- **Recommendation**: 12 for forensic provenance

---

## Environment-Specific Configurations

### Development (Local Anvil)
```env
RPC_URL=http://127.0.0.1:8545
CHAIN_ID=31337
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

### Testnet (Polygon Amoy)
```env
RPC_URL=https://rpc-amoy.polygon.technology/
CHAIN_ID=80002
PRIVATE_KEY=0x... (your testnet account)
CONTRACT_ADDRESS=0x... (deployed contract)
```

### Production
```env
RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
CHAIN_ID=137
PRIVATE_KEY= (load from vault, never hardcode)
CONTRACT_ADDRESS=0x... (mainnet deployment)
```

---

## Troubleshooting

### "OSINT engine failure: No API keys configured"
**Solution**: Configure at least one of `SERPAPI_KEY` or `BING_VISUAL_SEARCH_KEY`

### "Blockchain client not connected"
**Solution**: 
1. Verify `RPC_URL` is accessible
2. Check `PRIVATE_KEY` format (must start with `0x`)
3. Ensure account has sufficient ETH for gas

### "IPFS pinning failed"
**Solution**:
1. Verify `PINATA_API_KEY` and `PINATA_SECRET_KEY`
2. Check Pinata account has available storage quota

### "No face detected in image"
**Solution**:
1. Ensure image contains a clear, frontal face
2. Lower `FACE_DETECTION_CONFIDENCE` threshold
3. Check image quality (not too blurry or dark)

---

## Security Best Practices

1. **Never commit `.env` to Git** - Add `.env` to `.gitignore`
2. **Rotate keys regularly** - Especially after team member changes
3. **Use secret managers** for production (AWS Secrets Manager, HashiCorp Vault)
4. **Limit API key scopes** - Only grant necessary permissions
5. **Monitor usage** - Set up alerts for unusual API activity
6. **Test with testnets first** - Never test on mainnet

---

## Getting Help

- Documentation: `docs/`
- GitHub Issues: https://github.com/your-org/TraceFace/issues
- Configuration Validation: `python -m cli.main verify --help`
