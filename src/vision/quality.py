
import cv2
import numpy as np


def calculate_blur_score(image: np.ndarray) -> float:
    """Calculates the Laplacian variance to determine blurriness."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def check_image_quality(
    image: np.ndarray, blur_threshold: float = 100.0
) -> tuple[bool, float]:
    """
    Checks if an image passes the quality gates.
    Returns (is_blurry, blur_score).
    """
    if image is None or image.size == 0:
        return True, 0.0

    blur_score = calculate_blur_score(image)
    is_blurry = blur_score < blur_threshold

    return is_blurry, blur_score
