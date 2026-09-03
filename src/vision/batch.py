"""
Batch Evaluation Module

This module orchestrates the processing of multiple candidate images against
a single query embedding. It incorporates logic for evaluating group photos,
filtering out extreme profile faces via 2D landmarks, and ranking results.
"""

from typing import Any

import cv2
import numpy as np

from src.vision.detector import FaceDetector
from src.vision.embedder import FaceEmbedder
from src.vision.matcher import compute_cosine_similarity
from src.vision.quality import check_image_quality


class BatchEvaluator:
    """
    Evaluates batches of candidate images to find the best match for a query.

    This class handles group photos by evaluating every face detected and
    applying geometric heuristics to discard unusable (extreme profile) faces.
    """

    def __init__(self, detector: FaceDetector, embedder: FaceEmbedder):
        """
        Initializes the BatchEvaluator.

        Args:
            detector (FaceDetector): The initialized FaceDetector instance.
            embedder (FaceEmbedder): The initialized FaceEmbedder instance.
        """
        self.detector = detector
        self.embedder = embedder

    def is_extreme_profile(
        self, landmarks: np.ndarray, threshold_ratio: float = 0.25
    ) -> bool:
        """
        Estimates yaw from 2D landmarks to filter out extreme profile faces.
        Landmarks shape: (5, 2) -> [left_eye, right_eye, nose, left_mouth, right_mouth]
        """
        if len(landmarks) < 5:
            return False

        left_eye_x = landmarks[0][0]
        right_eye_x = landmarks[1][0]
        nose_x = landmarks[2][0]

        # Ensure nose is horizontally between eyes for a frontal face
        if not (min(left_eye_x, right_eye_x) <= nose_x <= max(left_eye_x, right_eye_x)):
            return True  # Nose is outside the eyes horizontally -> severe profile

        # Distances from nose to eyes
        d1 = abs(nose_x - left_eye_x)
        d2 = abs(right_eye_x - nose_x)

        if max(d1, d2) == 0:
            return True

        ratio = min(d1, d2) / max(d1, d2)
        return ratio < threshold_ratio

    def evaluate_candidates(
        self, query_embedding: np.ndarray, candidate_paths: list[str]
    ) -> list[dict[str, Any]]:
        """
        Evaluates a batch of candidate images against a query embedding.
        Returns a list of match results sorted by similarity descending.
        """
        results = []

        for path in candidate_paths:
            img = cv2.imread(path)
            if img is None:
                continue

            is_blurry, _ = check_image_quality(img)
            if is_blurry:
                # We can skip or record low quality
                results.append(
                    {"path": path, "similarity": 0.0, "error": "rejected_quality"}
                )
                continue

            # Use raw face analysis to find ALL faces in the candidate image
            # because detector.detect_face only returns the largest one
            faces = self.detector.app.get(img)
            if not faces:
                results.append(
                    {"path": path, "similarity": 0.0, "error": "no_face_detected"}
                )
                continue

            best_sim = 0.0
            best_face = None

            for face in faces:
                if self.is_extreme_profile(face.kps):
                    continue

                emb = face.embedding
                if emb is None:
                    continue

                norm = np.linalg.norm(emb)
                if norm != 0:
                    emb = emb / norm

                sim = compute_cosine_similarity(query_embedding, emb)
                if sim > best_sim:
                    best_sim = sim
                    best_face = face

            if best_face is None:
                results.append(
                    {"path": path, "similarity": 0.0, "error": "all_faces_rejected"}
                )
            else:
                results.append(
                    {
                        "path": path,
                        "similarity": best_sim,
                        "bbox": best_face.bbox.tolist(),
                        "landmarks": best_face.kps.tolist(),
                    }
                )

        # Sort by best similarity
        results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
        return results
