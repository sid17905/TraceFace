"""
Face Detection Module

This module is responsible for locating faces within an image and extracting
their bounding boxes and 5-point facial landmarks. It uses the RetinaFace
model (via InsightFace) to achieve highly accurate, view-invariant detection.
"""

import os
import sys
import warnings
from typing import Any

import insightface
import numpy as np

# Suppress insightface third-party FutureWarnings
warnings.filterwarnings(
    "ignore", category=FutureWarning, module="insightface.utils.face_align"
)


class FaceDetector:
    """
    RetinaFace detector wrapper for finding faces and 5-point landmarks.

    This class loads the RetinaFace detection module from the provided
    model pack and configures it to run on the CPU to extract bounding
    boxes and landmarks.
    """

    def __init__(self, model_name: str = "buffalo_l", ctx_id: int = 0):
        """
        Initializes the FaceDetector with the specified InsightFace model.

        Args:
            model_name (str, optional): Name of the model pack to load. Defaults to "buffalo_l".
            ctx_id (int, optional): Context ID. <= 0 means CPU. Defaults to 0.
        """
        # Suppress insightface hardcoded print statements
        original_stdout = sys.stdout
        with open(os.devnull, "w") as devnull:
            sys.stdout = devnull
            try:
                self.app = insightface.app.FaceAnalysis(
                    name=model_name,
                    allowed_modules=["detection"],
                    providers=["CPUExecutionProvider"],
                )
            finally:
                sys.stdout = original_stdout

        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))

    def detect_face(self, image: np.ndarray) -> dict[str, Any]:
        """
        Detects the most prominent face in the image based on bounding box area.

        Args:
            image (np.ndarray): The input image array in BGR format.

        Returns:
            dict[str, Any]: A dictionary containing:
                - 'bbox' (list[int]): Bounding box coordinates [x_min, y_min, x_max, y_max].
                - 'landmarks' (list[list[int]]): 5-point facial landmarks.
                - 'confidence' (float): Detection confidence score (0 to 1).

        Raises:
            ValueError: If no faces are detected in the image.
        """
        faces = self.app.get(image)
        if not faces:
            raise ValueError("ERR_NO_FACE_DETECTED")

        # If multiple faces, pick the largest bounding box area
        faces = sorted(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            reverse=True,
        )
        face = faces[0]

        bbox = face.bbox.astype(int)  # [x_min, y_min, x_max, y_max]
        kps = face.kps.astype(int)  # 5x2 array

        return {
            "bbox": bbox.tolist(),
            "landmarks": kps.tolist(),
            "confidence": float(face.det_score),
        }
