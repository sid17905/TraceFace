"""
Biometric Matching Module

This module handles the mathematical comparison between 512-dimensional
biometric vectors extracted by the ArcFace embedder. It computes Cosine
Similarity and Euclidean Distance, enforcing strict matching thresholds.
"""

import numpy as np


def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes the cosine similarity between two unit-normalized embedding vectors.

    Args:
        vec1 (np.ndarray): The first embedding vector.
        vec2 (np.ndarray): The second embedding vector.

    Returns:
        float: The cosine similarity score, ranging from -1.0 to 1.0.
    """
    v1 = np.asarray(vec1).flatten()
    v2 = np.asarray(vec2).flatten()

    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def compute_euclidean_distance(similarity: float) -> float:
    """Computes Euclidean distance derived from cosine similarity for unit vectors."""
    # d = sqrt(2 * (1 - Sc))
    val = 2.0 * (1.0 - similarity)
    return float(
        np.sqrt(max(0.0, val))
    )  # max(0.0, val) to prevent precision errors giving negatives


def is_authentic_match(similarity: float, threshold: float = 0.68) -> bool:
    """Returns True if the similarity strictly meets or exceeds the threshold."""
    return similarity >= threshold


def compute_match_confidence(similarity: float) -> float:
    """Computes a match confidence percentage."""
    conf = (similarity - 0.4) * 166.6
    return float(max(0.0, min(100.0, conf)))
