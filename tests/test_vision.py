import os

import cv2
import numpy as np
import pytest

from src.vision.detector import FaceDetector
from src.vision.embedder import FaceEmbedder
from src.vision.matcher import compute_cosine_similarity, is_authentic_match
from src.vision.quality import check_image_quality


def test_quality_check():
    # Create a random noise image (should not be blurry according to variance, but let's test it)
    img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    is_blurry, score = check_image_quality(img)
    assert isinstance(is_blurry, bool)
    assert isinstance(score, float)

    # Create a flat image (very blurry)
    flat_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    is_blurry, score = check_image_quality(flat_img, blur_threshold=100.0)
    assert is_blurry == True
    assert score < 100.0


@pytest.fixture(scope="module")
def detector():
    return FaceDetector()


@pytest.fixture(scope="module")
def embedder():
    return FaceEmbedder()


def test_detector_and_embedder(detector, embedder):
    # Try to test with a real image if we have one in data/sample_inputs/
    sample_path = "data/sample_inputs/sample_target.jpg"
    if not os.path.exists(sample_path):
        # Fallback to another file if available
        available_files = (
            [f for f in os.listdir("data/sample_inputs/") if f.endswith(".jpg")]
            if os.path.exists("data/sample_inputs/")
            else []
        )
        if available_files:
            sample_path = os.path.join("data/sample_inputs/", available_files[0])

    try:
        img = cv2.imread(sample_path)
        if img is None:
            pytest.skip("Sample image not found or unreadable")

        result = detector.detect_face(img)
        assert "bbox" in result
        assert "landmarks" in result

        emb = embedder.get_embedding(img, result["bbox"], result["landmarks"])
        assert emb.shape == (512,)

        hashes = embedder.compute_hashes(emb, img)
        assert "sha256" in hashes
        assert "keccak256" in hashes
        assert "phash" in hashes

    except ValueError as e:
        if str(e) == "ERR_NO_FACE_DETECTED":
            pytest.skip("No face detected in sample image")
        else:
            raise


def test_matcher():
    vec1 = np.random.rand(512)
    vec1 = vec1 / np.linalg.norm(vec1)

    vec2 = vec1.copy()

    sim = compute_cosine_similarity(vec1, vec2)
    assert np.isclose(sim, 1.0)
    is_match = is_authentic_match(sim, threshold=0.68)
    assert is_match

    vec3 = -vec1
    sim2 = compute_cosine_similarity(vec1, vec3)
    is_match2 = is_authentic_match(sim2, threshold=0.68)
    # The dummy vectors are completely different, should be low similarity
    assert sim2 < 0.45
    assert not is_match2


def test_liveness():
    import numpy as np

    from src.vision.liveness import FrequencyForensics

    analyzer = FrequencyForensics()
    # Test with empty image
    is_deepfake, score = analyzer.analyze_liveness(np.array([]))
    assert not is_deepfake

    # Test with random noise image (should have flat spectrum, might trigger deepfake depending on threshold, but let's just make sure it runs)
    dummy_img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    is_deepfake, score = analyzer.analyze_liveness(dummy_img)
    assert isinstance(is_deepfake, bool)
    assert isinstance(score, float)
