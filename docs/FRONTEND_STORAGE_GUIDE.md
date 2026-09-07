# 📱 How to View & Add Graphs in Frontend

## 🎯 **Quick Answer:**

### **View Stored Graphs:**
1. Open frontend: http://localhost:5173
2. Click **"7. Storage Browser"** tab
3. Browse all stored graphs
4. Click any graph to visualize

### **Add New Graphs:**
1. Click **"Storage Browser"** tab
2. Switch to **"Add New Graph"** sub-tab
3. Upload an image (drag & drop or click)
4. Click **"Scan & Create Graph"**
5. Watch real-time pipeline progress
6. Graph auto-saves when complete!

---

## 📊 **Complete Guide:**

### **Tab 1: Browse Stored Graphs** 📂

**What You'll See:**
```
💾 Stored Provenance Graphs
   
Job List:
  📋 demo_467faec63b86...     ✅ completed
     Nodes: 3 | Edges: 2
     Created: 2026-09-06 18:59:29
     
  📋 demo_3bb08fa43df4...     ✅ completed
     Nodes: 3 | Edges: 2
     Created: 2026-09-06 18:58:09
     
  [More jobs...]
```

**Actions:**
- ✅ **Click any job** → Loads the graph visualization
- 🔄 **Refresh button** → Reload stored graphs
- 📊 **View details** → See node count, edge count, timestamps

**After Selecting a Graph:**
- D3.js force layout visualization appears
- Shows all platforms (Twitter, Reddit, Instagram, YouTube, TikTok, Facebook)
- Highlights ROOT-ZERO (original source)
- Shows propagation path
- Displays time deltas and hamming distances

---

### **Tab 2: Add New Graph** ➕

**Step 1: Upload Image**
```
📁 Drop an image here or click to upload
Accepts: JPG, PNG, WebP (max 15MB)
```

**Options:**
- Drag & drop image file
- Click to open file picker
- Supports JPG, PNG, WebP

**Step 2: Scan**
```
🔍 Scan & Create Graph
```

**What Happens:**
1. ✅ Face Extraction (RetinaFace detection)
2. ✅ Liveness Gate (Deepfake check)
3. ✅ OSINT Crawl (Multi-engine search)
4. ✅ Biometric Gate (Similarity verification)
5. ✅ Merkle Seal (Cryptographic hashing)
6. ✅ IPFS Pin (Decentralized storage)
7. ✅ Blockchain Anchor (Permanent attestation)

**Real-Time Progress:**
```
Pipeline Progress:
  ✅ face extraction
  ⏳ osint crawl
  ⏸️ biometric gate
  ⏸️ merkle seal
  ⏸️ ipfs pin
  ⏸️ blockchain anchor
```

**Step 3: Completion**
```
✅ Scan Complete!
  
Job ID: job_fad564ccaa23491e
Scan ID: urn:uuid:c73508c3-900c...
Similarity: 0.914
```

**Step 4: Auto-Load**
- Graph automatically loads in visualization
- Switches to "Browse" tab
- Shows your new graph

---

## 🔧 **Backend API Endpoints:**

### **List All Stored Graphs**
```bash
GET /api/v1/graph/jobs
```

Response:
```json
{
  "jobs": [
    {
      "job_id": "demo_467faec63b86",
      "scan_id": "urn:uuid:5562049f...",
      "status": "completed",
      "created_at": "2026-09-06T18:59:29...",
      "nodes_count": 3,
      "edges_count": 2
    }
  ],
  "total": 8
}
```

### **Load Specific Graph**
```bash
GET /api/v1/graph/job/{job_id}
```

Response:
```json
{
  "job_id": "demo_467faec63b86",
  "graph": {
    "nodes": [
      {
        "node_id": "origin_root_b42e58ff",
        "platform": "Twitter/X",
        "author_handle": "@original_creator",
        "is_root_zero": true
      }
    ],
    "edges": [...]
  }
}
```

### **Find Similar by pHash**
```bash
GET /api/v1/graph/similar/{phash}?max_hamming=12
```

---

## 📝 **Alternative: CLI Method**

### **Create via CLI:**
```bash
python -m cli.main demo
```

### **View in DB:**
```bash
python -c "
import sqlite3
c = sqlite3.connect('.cache/provenance.db').cursor()
c.execute('SELECT COUNT(*) FROM origin_nodes')
print('Stored nodes:', c.fetchone()[0])
"
```

---

## 🎨 **Graph Visualization Features:**

### **Interactive Controls:**
- 🔍 Zoom in/out (scroll)
- 🖱️ Pan (drag)
- 👆 Click node → Select
- 🎯 Drag nodes → Reposition

### **Color Coding:**
- 🔵 **Twitter** - #1DA1F2
- 🟠 **Reddit** - #FF4500
- 🟣 **Instagram** - #E4405F
- 🔷 **LinkedIn** - #0A66C2
- 🔴 **YouTube** - #FF0000
- ⚫ **TikTok** - #000000
- 🔵 **Facebook** - #1877F2

### **Root-Zero Highlighting:**
- 🏛️ **Gold border** - Original source
- ⭐ **Larger size** - Most important node
- 📍 **"Root-Zero" label** - Clear marking

---

## 🚀 **Workflow Example:**

### **Complete Session:**
```
1. Open http://localhost:5173
2. Click "7. Storage Browser"
3. See previous runs (if any)
4. Switch to "Add New Graph"
5. Upload face image
6. Watch pipeline progress
7. See graph auto-load
8. Explore visualization
9. Return to "Browse" tab
10. See your new graph in the list!
```

---

## 💡 **Pro Tips:**

1. **Batch Creation**: Run demo multiple times to see accumulation
2. **Compare Graphs**: Load multiple graphs to see different propagation patterns
3. **Platform Filter**: Use platform colors to identify sources
4. **Time Analysis**: Check time deltas to see how fast content spreads
5. **Export**: Use API endpoints to export graph data

---

## ✅ **Success Indicators:**

- ✅ **Database grows** each run
- ✅ **Nodes accumulate** (not overwritten)
- ✅ **Edges connect** nodes properly
- ✅ **ROOT-ZERO** identified correctly
- ✅ **Visualization** renders interactively

---

## 🐛 **Troubleshooting:**

**Empty graph list?**
- Run `python -m cli.main demo` first
- Check `.cache/provenance.db` exists

**Graph not loading?**
- Check backend API is running (http://127.0.0.1:8000/health)
- Verify job status is "completed"

**Visualization not rendering?**
- Check browser console for errors
- Verify D3.js loaded (check Network tab)

---

**Your stored graphs are now fully accessible in the frontend! 🎉**
