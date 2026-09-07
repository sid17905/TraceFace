# 🚀 TraceFace Production Deployment Checklist

Complete guide to deploy TraceFace from development to production.

---

## 📋 Pre-Deployment Checklist

### ✅ Code Quality
- [x] All hardcoded mock data removed
- [x] Persistent storage implemented (SQLite)
- [x] Multi-source OSINT aggregation working
- [x] All 101 tests passing
- [x] No simulated blockchain fallbacks
- [x] Frontend error handling implemented
- [x] Configuration documentation complete

### ✅ Security
- [ ] `.env` file added to `.gitignore` (NEVER commit secrets)
- [ ] Private keys loaded from secure vault (AWS Secrets Manager, HashiCorp Vault)
- [ ] API keys rotated before production deployment
- [ ] Rate limiting configured for OSINT engines
- [ ] HTTPS enabled on API server
- [ ] CORS origins restricted to your domain
- [ ] SSL/TLS certificates configured

### ✅ Infrastructure
- [ ] Dedicated server/VM provisioned (min 4GB RAM, 2 CPU)
- [ ] Python 3.14+ installed
- [ ] Node.js 18+ installed
- [ ] InsigntFace models downloaded (~150MB)
- [ ] SQLite database directory created (`.cache/`)
- [ ] Log rotation configured
- [ ] Monitoring/alerting set up (Prometheus, Grafana, Datadog)

---

## 🔧 Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/TraceFace.git
cd TraceFace
```

### 2. Copy Environment Template
```bash
cp .env.example .env
nano .env  # Fill in your production values
```

### 3. Install Python Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 4. Install Node.js Dependencies
```bash
npm install
```

### 5. Download InsightFace Models
```bash
python -c "from src.vision.detector import FaceDetector; FaceDetector()"
```

---

## 🔑 Configuration

### Required Keys (Testnet)

```env
# OSINT Multi-Source (at least one required)
SERPAPI_KEY=your_serpapi_production_key
BING_VISUAL_SEARCH_KEY=your_bing_production_key

# Blockchain
RPC_URL=https://polygon-amoy.g.alchemy.com/v2/YOUR_KEY
CHAIN_ID=80002
PRIVATE_KEY=0x...  # Load from vault, never hardcode
CONTRACT_ADDRESS=0x...  # Deployed contract

# IPFS
PINATA_API_KEY=your_production_pinata_key
PINATA_SECRET_KEY=your_production_pinata_secret
```

### Required Keys (Mainnet)

```env
# OSINT
SERPAPI_KEY=your_production_serpapi_key
BING_VISUAL_SEARCH_KEY=your_production_bing_key

# Blockchain
RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
CHAIN_ID=137
PRIVATE_KEY=0x...  # Production deployer account
CONTRACT_ADDRESS=0x...  # Mainnet deployment

# IPFS
PINATA_API_KEY=your_production_pinata_key
PINATA_SECRET_KEY=your_production_pinata_secret
```

---

## 🏗️ Smart Contract Deployment

### Testnet (Polygon Amoy)

```bash
# Deploy to testnet
npx hardhat run contracts/scripts/deploy.js --network amoy

# Copy deployed address to .env
CONTRACT_ADDRESS=0x...
```

### Mainnet (Polygon)

```bash
# Deploy to mainnet
npx hardhat run contracts/scripts/deploy.js --network polygon

# Copy deployed address to .env
CONTRACT_ADDRESS=0x...
```

⚠️ **IMPORTANT**: Verify contract on block explorer before use

---

## 🏃 Running the Application

### Backend API Server

```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production (with Gunicorn)
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or use the built-in production server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Development Server

```bash
cd frontend
npm run dev
```

### Frontend Production Build

```bash
cd frontend
npm run build
npm run preview  # Preview production build
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Storage tests
pytest tests/test_provenance_store.py -v

# OSINT multi-source tests
pytest tests/test_osint.py -v

# API pipeline tests
pytest tests/test_api_pipeline.py -v
```

### Integration Test
```bash
# Test with sample image
python -m cli.main scan --image data/sample_inputs/sample_target.jpg
```

---

## 📊 Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "service": "traceface-api",
  "status": "healthy",
  "version": "1.0.0",
  "vision_loaded": true,
  "blockchain_connected": true,
  "contract_deployed": true
}
```

### Graph Endpoints
```bash
# Load persisted graph by job_id
curl http://localhost:8000/api/v1/graph/job/{job_id}

# Find similar nodes by pHash
curl http://localhost:8000/api/v1/graph/similar/{phash}?max_hamming=12
```

### Metrics to Monitor
- API response times (< 500ms)
- OSINT engine success rates (> 90%)
- Blockchain transaction success rate (100%)
- IPFS pin success rate (100%)
- Error rates (< 1%)
- Database size (< 10GB)

---

## 🔒 Security Best Practices

### 1. Secret Management
```bash
# Load private key from AWS Secrets Manager
PRIVATE_KEY=$(aws secretsmanager get-secret-value --secret-id traceface/private_key --query SecretString --output text)

# Or from environment
export PRIVATE_KEY=$(cat /run/secrets/private_key)
```

### 2. HTTPS Configuration
```nginx
server {
    listen 443 ssl;
    server_name api.traceface.com;

    ssl_certificate /etc/letsencrypt/live/traceface.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/traceface.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Rate Limiting
```python
# Add to api/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/scan/upload")
@limiter.limit("10/minute")
async def scan_upload():
    ...
```

### 4. CORS Configuration
```python
# Update api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://traceface.com"],  # Production domain only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 🐛 Troubleshooting

### Issue: "Blockchain client not connected"
**Solution**:
1. Verify `RPC_URL` is accessible: `curl $RPC_URL -X POST -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'`
2. Check `PRIVATE_KEY` format (must start with `0x`)
3. Ensure account has ETH for gas

### Issue: "OSINT engine failure: No API keys configured"
**Solution**:
1. Add at least one of `SERPAPI_KEY` or `BING_VISUAL_SEARCH_KEY` to `.env`
2. Restart API server
3. Test: `python -m cli.main scan --image data/sample_inputs/sample_target.jpg`

### Issue: "No face detected in image"
**Solution**:
1. Ensure image has frontal face
2. Adjust `FACE_DETECTION_CONFIDENCE` threshold (default: 0.85)
3. Check image quality (not too blurry/dark)

### Issue: "IPFS pinning failed"
**Solution**:
1. Verify Pinata credentials
2. Check account storage quota
3. Test manually: `curl -X POST "https://api.pinata.cloud/pinning/pinJSONToIPFS" -H "pinata_api_key: $PINATA_API_KEY" -H "pinata_secret_api_key: $PINATA_SECRET_KEY" -d '{"test":"data"}'`

### Issue: Database locked errors
**Solution**:
1. Ensure only one API worker (or use PostgreSQL instead)
2. Add connection pooling
3. Or upgrade to PostgreSQL for multi-worker setups

---

## 🚀 Production Deployment

### Option 1: Docker

```dockerfile
# Dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t traceface:latest .
docker run -p 8000:8000 --env-file .env traceface:latest
```

### Option 2: Systemd Service

```bash
# /etc/systemd/system/traceface-api.service
[Unit]
Description=TraceFace API Server
After=network.target

[Service]
Type=simple
User=traceface
WorkingDirectory=/opt/traceface
Environment="PATH=/opt/traceface/.venv/bin"
ExecStart=/opt/traceface/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable traceface-api
sudo systemctl start traceface-api
```

### Option 3: Cloud Deployment

**AWS EC2**:
```bash
# Launch EC2 instance (t3.medium recommended)
# SSH into instance
# Follow "Environment Setup" steps above
# Configure security group to allow port 8000
```

**Google Cloud Run**:
```bash
gcloud run deploy traceface \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars-file .env
```

**Railway/Render**:
```bash
# Connect GitHub repo
# Set environment variables in dashboard
# Deploy
```

---

## 📈 Scaling

### Vertical Scaling
- Increase CPU cores (more workers)
- Increase RAM (larger models)
- Use SSD for database

### Horizontal Scaling
- Use PostgreSQL instead of SQLite
- Add Redis for session storage
- Use load balancer (nginx, HAProxy)
- Deploy multiple instances

### Performance Tuning
```env
# .env
DEVICE=cuda  # Use GPU for 3-5x speedup
SEARCH_MAX_CANDIDATES=15  # Balance coverage vs speed
DOWNLOAD_CONCURRENCY=12  # Increase for faster downloads
MAX_UPLOAD_BYTES=20971520  # 20MB if server has more RAM
```

---

## 🎯 Go-Live Checklist

✅ All tests passing  
✅ Environment variables configured  
✅ Smart contract deployed  
✅ Contract address updated in `.env`  
✅ Private key loaded from vault  
✅ HTTPS configured  
✅ Monitoring set up  
✅ Log rotation configured  
✅ Backup strategy in place  
✅ Error alerting configured  
✅ Rate limiting enabled  
✅ CORS restricted to domain  
✅ Health check endpoint working  
✅ Sample scan successful  
✅ Graph persistence verified  
✅ Multi-source OSINT working  

---

## 📞 Support

- Documentation: `docs/CONFIGURATION.md`
- GitHub Issues: https://github.com/your-org/TraceFace/issues
- Health Check: `GET /health`

---

**You're ready for production! 🎉**
