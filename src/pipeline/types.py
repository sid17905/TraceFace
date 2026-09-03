from pydantic import BaseModel, Field
from typing import List, Tuple, Optional
from datetime import datetime

class QualityMetrics(BaseModel):
    laplacian_blur_score: float
    is_blurry: bool
    confidence_score: float

class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    landmarks_5pt: List[Tuple[int, int]]

class FaceScanOutput(BaseModel):
    scan_id: str
    timestamp_utc: str
    source_image_path: str
    image_hash_sha256: str
    quality_metrics: QualityMetrics
    bounding_box: BoundingBox
    embedding_vector: List[float]
    embedding_hash_keccak256: str
    perceptual_hash_phash: str
