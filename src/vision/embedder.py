import cv2
import numpy as np
import insightface
from Crypto.Hash import SHA256, keccak
import imagehash
from PIL import Image
from typing import Dict, List, Optional
import warnings
import sys
import os

# Suppress insightface third-party FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning, module="insightface.utils.face_align")

class FaceEmbedder:
    """
    ArcFace embedder wrapper for extracting 512-D vectors and computing cryptographic hashes.
    """
    def __init__(self, model_name: str = 'buffalo_l', ctx_id: int = 0):
        # We instantiate with detection and recognition to satisfy FaceAnalysis assertions
        # Suppress insightface hardcoded print statements
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            self.app = insightface.app.FaceAnalysis(
                name=model_name, 
                allowed_modules=['detection', 'recognition'],
                providers=['CPUExecutionProvider']
            )
        finally:
            sys.stdout.close()
            sys.stdout = original_stdout
            
        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        self.recognition_model = self.app.models['recognition']
        
    def get_embedding(self, image: np.ndarray, bbox: List[int], landmarks: List[List[int]]) -> np.ndarray:
        """
        Extracts the 512-D normalized embedding vector.
        Requires the original image and the bounding box/landmarks from the detector.
        """
        class MockFace:
            def __init__(self, b, k):
                self.bbox = np.array(b)
                self.kps = np.array(k)
                self.embedding = None
                
        face = MockFace(bbox, landmarks)
        # The recognition model modifies the face object in place to add the embedding
        self.recognition_model.get(image, face)
        
        if not hasattr(face, 'embedding') or face.embedding is None:
            raise ValueError("Failed to generate embedding")
            
        emb = face.embedding
        norm = np.linalg.norm(emb)
        if norm != 0:
            emb = emb / norm
            
        return emb

    def compute_hashes(self, embedding: np.ndarray, image: np.ndarray) -> Dict[str, str]:
        """
        Computes the Keccak-256 and SHA-256 hashes of the embedding,
        and the perceptual hash (pHash) of the original image.
        """
        emb_bytes = embedding.astype(np.float32).tobytes()
        
        # SHA-256
        sha256_hash = SHA256.new(emb_bytes).hexdigest()
        
        # Keccak-256
        k_hash = keccak.new(digest_bits=256)
        k_hash.update(emb_bytes)
        keccak_hash = "0x" + k_hash.hexdigest()
        
        # Perceptual hash (pHash)
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        p_hash = str(imagehash.phash(pil_img))
        
        return {
            'sha256': sha256_hash,
            'keccak256': keccak_hash,
            'phash': p_hash
        }
