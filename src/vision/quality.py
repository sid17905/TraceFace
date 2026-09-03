"""
Quality Assessment Module

This module provides utility functions for evaluating the visual quality
of input images before they are passed into the deep learning pipeline.
It helps filter out images that are too blurry or distorted, saving
compute time and preventing false positives in biometric matching.
"""

import cv2
import numpy as np


def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculates the Laplacian variance of an image to determine its blurriness.

    The Laplacian operator highlights regions of rapid intensity change (edges).
    A lower variance indicates fewer edges, implying a blurrier image.

    Args:
        image (np.ndarray): The input image array in BGR format.

    Returns:
        float: The Laplacian variance score. Higher is sharper.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def check_image_quality(
    image: np.ndarray, blur_threshold: float = 100.0
) -> tuple[bool, float]:
    """
    Evaluates if an image passes the minimum quality gates required for facial recognition.

    Args:
        image (np.ndarray): The input image array in BGR format.
        blur_threshold (float, optional): The minimum Laplacian variance score
            required to pass. Defaults to 100.0.

    Returns:
        tuple[bool, float]: A tuple containing:
            - is_blurry (bool): True if the image is considered too blurry.
            - blur_score (float): The actual Laplacian variance score computed.
    """
    if image is None or image.size == 0:
        return True, 0.0

    blur_score = calculate_blur_score(image)
    is_blurry = blur_score < blur_threshold

    return is_blurry, blur_score
