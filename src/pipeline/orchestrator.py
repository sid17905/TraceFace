import uuid
from datetime import datetime, timezone

import cv2

from src.pipeline.types import BoundingBox, FaceScanOutput, QualityMetrics
from src.vision.detector import FaceDetector
from src.vision.embedder import FaceEmbedder
from src.vision.quality import check_image_quality


class VisionPipeline:
    def __init__(self):
        # Initialize the singletons
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()

    def process_query_image(self, image_path: str) -> FaceScanOutput | None:
        """
        Runs the full vision pipeline on a target query image.
        Returns the FaceScanOutput data model or None if it fails.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image at {image_path}")

        is_blurry, blur_score = check_image_quality(img)

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
