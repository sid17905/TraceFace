import numpy as np

from src.crypto.quantizer import (
    THRESHOLD_SCALED,
    compute_scaled_dot_product,
    dequantize_vector,
    quantize_vector,
    verify_quantized_match,
)
from src.crypto.zk_prover import ZkBiometricProver


def test_vector_quantization():
    vec = [0.123456, -0.654321, 0.999999, 0.0]
    quant = quantize_vector(vec)
    assert quant == [1235, -6543, 10000, 0]

    dequant = dequantize_vector(quant)
    assert len(dequant) == len(vec)
    assert abs(dequant[0] - 0.1235) < 1e-4


def test_scaled_dot_product_and_match():
    np.random.seed(42)
    v1 = np.random.randn(512)
    v1 = v1 / np.linalg.norm(v1)

    v2 = v1 + np.random.normal(0, 0.02, 512)
    v2 = v2 / np.linalg.norm(v2)

    cosine_sim = float(np.dot(v1, v2))
    assert cosine_sim > 0.68

    q1 = quantize_vector(v1)
    q2 = quantize_vector(v2)

    dot = compute_scaled_dot_product(q1, q2)
    assert dot >= THRESHOLD_SCALED
    assert verify_quantized_match(q1, q2) is True


def test_zk_prover_proof_generation_and_verification():
    np.random.seed(123)
    v1 = np.random.randn(512)
    v1 = (v1 / np.linalg.norm(v1)).tolist()

    v2 = list(v1)

    prover = ZkBiometricProver()
    proof_payload = prover.generate_proof(v1, v2, threshold=0.68)

    assert proof_payload["is_valid_match"] is True
    assert proof_payload["publicSignals"][0] == "1"
    assert prover.verify_proof(proof_payload) is True

    a, b, c, inputs = prover.format_for_solidity(proof_payload)
    assert len(a) == 2
    assert len(b) == 2
    assert len(c) == 2
    assert len(inputs) == 3
    assert inputs[0] == 1


def test_zk_prover_rejects_dissimilar_vectors():
    np.random.seed(456)
    v1 = np.random.randn(512)
    v1 = (v1 / np.linalg.norm(v1)).tolist()

    v2 = (-np.array(v1)).tolist()

    prover = ZkBiometricProver()
    proof_payload = prover.generate_proof(v1, v2, threshold=0.68)

    assert proof_payload["is_valid_match"] is False
    assert proof_payload["publicSignals"][0] == "0"
    assert prover.verify_proof(proof_payload) is False
