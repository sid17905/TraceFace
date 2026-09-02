# 🎯 Member 1 Execution Plan: Computer Vision & Biometric Systems Engineer
**Role:** AI / Biometrics Lead  
**Focus:** Face Localization, Landmark Alignment, ArcFace Embeddings, Anti-Spoofing & Biometric Verification  
**Sprint Duration:** 3 Days (Hackathon Ready)  

---

## 1. Technological Maneuvers & High-Grade Innovations
1. **RetinaFace with ResNet50 Backbone:** Sub-millisecond face bounding box localization with 5-point facial landmark keypoints (left eye, right eye, nose, left mouth corner, right mouth corner).
2. **5-Point Affine Landmark Alignment:** Rotates and normalizes facial crops to a canonical $112 \times 112$ grid to ensure view-invariant biometric extraction.
3. **InsightFace ArcFace (buffalo_l model):** Extracts normalized 512-dimensional continuous biometric vectors on a hypersphere ($L_2$ unit norm).
4. **Laplacian Variance Quality Filter:** Automatically detects blurry or out-of-focus images before hitting search APIs, ensuring zero wasted API calls.
5. **Dual-Metric Matcher (Cosine + Euclidean L2):** Real-time comparison between query scan and scraped social media candidate images with strict threshold validation ($S_c \ge 0.68$).
6. **Perceptual Image Hashing (pHash):** 64-bit DCT-based frequency domain hashing alongside deep embeddings for structural image integrity verification.

---

## 2. 3-Day Hour-by-Hour Roadmap

### Day 1: Vision Pipeline, Landmark Alignment & Embedding Engine
* **09:00 - 11:00 (Env Setup & Model Weights):**
  - Setup Python 3.11 virtual environment.
  - Install `insightface`, `onnxruntime`, `opencv-python`, `numpy`, `pillow`, `imagehash`.
  - Download and verify `buffalo_l` ONNX model weights in local cache (`~/.insightface/models/`).
* **11:00 - 14:00 (RetinaFace & Quality Filter):**
  - Implement `src/vision/quality.py`: Compute Laplacian variance, luminance histogram, and minimum resolution gating.
  - Implement `src/vision/detector.py`: Face detection, bounding box extraction, and 5-point affine transformation matrix calculation.
* **14:00 - 15:00:** Lunch & Team Sync 1 (Confirm data schemas from `COMMON_REFERENCE.md`).
* **15:00 - 18:00 (ArcFace Vector Embedder):**
  - Implement `src/vision/embedder.py`: Feed normalized face crop to ArcFace model; extract 512-dimensional float32 vector; normalize to unit length ($\|v\|_2 = 1$).
  - Compute Keccak-256 and SHA-256 hashes of the embedding float array.
* **18:00 - 20:00 (Unit Tests & Benchmarking):**
  - Write `tests/test_vision.py`.
  - Benchmark extraction speed (Target: $< 120\text{ms}$ on CPU, $< 25\text{ms}$ on GPU).
  - Deliverable: `FaceScanOutput` model serialized to JSON.

---

### Day 2: Cross-Verification Engine & Candidate Ingestion
* **09:00 - 12:00 (Biometric Cross-Matcher):**
  - Implement `src/vision/matcher.py`:
    - Compute Cosine Similarity: $S_c = \mathbf{u} \cdot \mathbf{v}$ (since vectors are unit normalized).
    - Compute Euclidean Distance: $d = \sqrt{2(1 - S_c)}$.
    - Compute Match Confidence Percentage: $\text{Confidence} = \max(0.0, \min(100.0, (S_c - 0.4) \times 166.6))$.
* **12:00 - 14:00 (In-Memory Batch Image Verification):**
  - Create a batch evaluation function that receives candidate image buffers downloaded by Member 2's scraper.
  - Run face detection on candidate images, align crops, compute embeddings, and return ranked match results.
* **14:00 - 15:00:** Lunch & Team Sync 2 (Integration test with Member 2's Google Lens scraper output).
* **15:00 - 18:00 (Robustness & Edge-Case Handling):**
  - Handle profile faces (yaw $> 45^\circ$), partial occlusions (sunglasses/masks), and group photos (select candidate with highest similarity).
* **18:00 - 20:00 (CLI Visuals):**
  - Build `cli/ui.py` Rich ASCII visualizer: Render face bounding box coordinates, landmark points, and biometric confidence gauge.

---

### Day 3: End-to-End Orchestration, Stress Testing & Submission Polish
* **09:00 - 12:00 (Full Pipeline Integration):**
  - Connect `src/vision/` outputs directly to `src/pipeline/orchestrator.py`.
  - Verify that query image vector seamlessly passes to Member 3's Merkle tree builder (`src/crypto/merkle.py`).
* **12:00 - 14:00 (End-to-End Stress Test):**
  - Test pipeline across 5 diverse test subjects (e.g., Satya Nadella, Sam Altman, Vitalik Buterin, and team members).
  - Ensure zero false positives and 100% true positive verification.
* **14:00 - 15:00:** Lunch & Team Sync 3 (Full dry run of demo video recording).
* **15:00 - 18:00 (Demo Recording & CLI Polish):**
  - Co-record the screen recording demonstrating the face scan step, landmark alignment logs, and similarity score output.
* **18:00 - 20:00 (README & Code Review):**
  - Write CV section in `README.md` explaining ArcFace, RetinaFace, and vector hashing.
  - Ensure all files pass `ruff` and `black`.

---

## 3. Key Deliverable Files
* `src/vision/detector.py`
* `src/vision/embedder.py`
* `src/vision/quality.py`
* `src/vision/matcher.py`
* `tests/test_vision.py`

---

## 4. Verification & Testing Checklist
- [ ] Face detection succeeds on high/low-light images.
- [ ] Quality gate catches and rejects blurred images with clear error message.
- [ ] Embedding vector is strictly 512 dimensions and unit-normalized.
- [ ] Cosine similarity between two different photos of the same person is $\ge 0.70$.
- [ ] Cosine similarity between two different people is $\le 0.45$.
- [ ] Unit tests pass via `pytest tests/test_vision.py`.
