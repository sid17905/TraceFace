"""
Data Types Module

This module contains the strict Pydantic schemas that define the data payloads
passed between the Vision, OSINT, and Web3 engines.
"""

from pydantic import BaseModel


class QualityMetrics(BaseModel):
    """Metrics regarding the visual quality of an image."""

    laplacian_blur_score: float
    is_blurry: bool
    confidence_score: float
    is_deepfake: bool
    deepfake_score: float


class BoundingBox(BaseModel):
    """Coordinates and facial landmarks for a detected face."""

    x_min: int
    y_min: int
    x_max: int
    y_max: int
    landmarks_5pt: list[tuple[int, int]]


class FaceScanOutput(BaseModel):
    """
    The unified data model containing all biometric extraction data.
    This model is serialized to JSON and stored on the blockchain via Merkle trees.
    """

    scan_id: str
    timestamp_utc: str
    source_image_path: str
    image_hash_sha256: str
    quality_metrics: QualityMetrics
    bounding_box: BoundingBox
    embedding_vector: list[float]
    embedding_hash_keccak256: str
    perceptual_hash_phash: str
