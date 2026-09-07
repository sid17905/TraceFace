"""
Pipeline Orchestrator Module

This module serves as the primary integration point between the Computer Vision
engine and the rest of the TraceFace system (OSINT and Web3 modules).
"""

import uuid
from datetime import datetime, timezone

import cv2

from src.pipeline.types import BoundingBox, FaceScanOutput, QualityMetrics
from src.vision.detector import FaceDetector
from src.vision.embedder import FaceEmbedder
from src.vision.liveness import FrequencyForensics
from src.vision.quality import check_image_quality


class VisionPipeline:
    """
    High-level orchestrator for the biometric vision pipeline.

    This class instantiates the singleton detectors and embedders,
    managing the full lifecycle of a facial scan from a raw image path
    to a fully populated FaceScanOutput data model.
    """

    def __init__(self):
        """
        Initializes the VisionPipeline and its underlying deep learning models.
        """
        # Initialize the singletons
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.liveness = FrequencyForensics()

    def process_query_image(self, image_path: str) -> FaceScanOutput | None:
        """
        Runs the full vision pipeline on a target query image.
        Returns the FaceScanOutput data model or None if it fails.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image at {image_path}")

        is_blurry, blur_score = check_image_quality(img)
        is_deepfake, df_score = self.liveness.analyze_liveness(img)

        # Frequency-domain liveness is a heuristic advisory, not a trained
        # classifier, so a positive flag is surfaced as a warning rather than
        # aborting the scan. Callers that need a hard gate (e.g. a strict
        # ingestion mode) can inspect quality_metrics.is_deepfake themselves.
        deepfake_warning = None
        if is_deepfake:
            deepfake_warning = (
                f"Frequency-forensics flagged possible synthetic artifacts "
                f"(anomaly score {df_score:.3f}). Treat provenance as unverified."
            )

        try:
            det_result = self.detector.detect_face(img)
        except ValueError as e:
            raise ValueError(f"Face detection failed: {e}")

        bbox = det_result["bbox"]
        landmarks = det_result["landmarks"]
        confidence = det_result["confidence"]

        emb = self.embedder.get_embedding(img, bbox, landmarks)
        hashes = self.embedder.compute_hashes(emb, img)

        output = FaceScanOutput(
            scan_id=f"urn:uuid:{uuid.uuid4()}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            source_image_path=image_path,
            image_hash_sha256=hashes["sha256"],
            quality_metrics=QualityMetrics(
                laplacian_blur_score=blur_score,
                is_blurry=is_blurry,
                confidence_score=confidence,
                is_deepfake=is_deepfake,
                deepfake_score=df_score,
                deepfake_warning=deepfake_warning,
            ),
            bounding_box=BoundingBox(
                x_min=bbox[0],
                y_min=bbox[1],
                x_max=bbox[2],
                y_max=bbox[3],
                landmarks_5pt=landmarks,
            ),
            embedding_vector=emb.tolist(),
            embedding_hash_keccak256=hashes["keccak256"],
            perceptual_hash_phash=hashes["phash"],
        )

        return output


# Main orchestrator entry point for the vision module
vision_pipeline = VisionPipeline()


def run_vision_pipeline(image_path: str) -> FaceScanOutput | None:
    return vision_pipeline.process_query_image(image_path)
