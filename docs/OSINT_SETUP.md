# OSINT Search Setup Guide

## Problem
You're seeing **"biometrics fail"** because no real OSINT candidates are being found.

## Root Cause
The internet search engines are not configured. Without API keys, the system cannot:
1. Search Google Lens for similar images
2. Search Bing Visual Search for matches
3. Find real social media posts with the face

## Required Setup

### 1. Get SerpApi Key (Recommended - Google Lens)

**Steps:**
1. Go to https://serpapi.com/
2. Create free account (100 searches/month free)
3. Get your API key from dashboard
4. Add to `.env`:

```bash
SERPAPI_KEY=your_serpapi_key_here
```

**Benefits:**
- Google Lens is the most comprehensive
- Finds matches across all platforms
- Social media prioritized

### 2. Alternative: Bing Visual Search

**Steps:**
1. Go to https://azure.microsoft.com/en-us/services/cognitive-services/bing-visual-search/
2. Create Azure account (free tier available)
3. Get API key
4. Add to `.env`:

```bash
BING_VISUAL_SEARCH_KEY=your_bing_key_here
```

### 3. Check Configuration

```bash
# Test if configured
python -c "from src.config import settings; print(f'SerpApi configured: {bool(settings.serpapi_key)}')"
```

## What Happens Without Keys

**Current Behavior:**
```
1. Upload image
2. Biometric gate fails (no candidates found)
3. Creates fallback "unknown" node
4. No real internet matches
```

**With Keys Configured:**
```
1. Upload image
2. Face extracted
3. Google Lens searches internet
4. Finds matching social media posts
5. Downloads candidate images
6. Biometric verification (cosine similarity)
7. Creates nodes for each verified match
8. Builds propagation graph (Twitter → Reddit → Instagram)
```

## Verification

After adding keys, restart backend and test:

```bash
# Restart backend
python -m uvicorn api.main:app --reload

# Test upload
python -c "
import requests
files = {'file': open('data/sample_inputs/sample_target.jpg', 'rb')}
data = {'run_osint': 'true'}
r = requests.post('http://127.0.0.1:8000/api/v1/scan/upload', files=files, data=data)
print(r.json())
"
```

## Expected Results

**Without Keys:**
- 1 node per upload (fallback/unknown)
- No propagation graph
- No time deltas

**With Keys:**
- Multiple nodes (Twitter, Reddit, Instagram, etc.)
- Full propagation graph with edges
- Time deltas and hamming distances
- Real social media URLs

## Cost

**SerpApi:**
- Free: 100 searches/month
- Pro: $50/month for 5,000 searches
- Enterprise: Custom pricing

**Bing:**
- Free: 1,000 transactions/month
- Standard: $1-3 per 1,000 transactions

## Alternative: Mock Mode

If you don't want to use real APIs, the batch graph creator works:

```bash
# Creates realistic mock graphs
python -c "
from src.storage.provenance_store import get_provenance_store
from src.pipeline.types import OriginNode, PropagationEdge, PropagationGraph
import uuid
from datetime import datetime, timezone, timedelta
import random

store = get_provenance_store()

# Create realistic mock graph (see batch push script above)
# This creates Twitter → Reddit → Instagram → YouTube paths
"
```

## Quick Fix Summary

1. **Get SerpApi key** from https://serpapi.com/
2. **Add to .env**: `SERPAPI_KEY=your_key`
3. **Restart backend**
4. **Upload image** - will now find real matches!

Your graphs will then contain actual internet nodes with real platform propagation! 
