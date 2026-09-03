from .canonicalizer import canonicalize_json
from .hasher import (
    hash_face_embedding,
    keccak256_bytes,
    keccak256_hex,
    sha256_bytes,
    sha256_file,
)
from .merkle import (
    ProvenanceMerkleResult,
    build_provenance_merkle_tree,
    verify_merkle_root,
)
from .quantizer import (
    SCALE_FACTOR,
    THRESHOLD_SCALED,
    compute_commitment,
    compute_scaled_dot_product,
    dequantize_vector,
    quantize_vector,
    verify_quantized_match,
)
from .zk_prover import ZkBiometricProver

__all__ = [
    "SCALE_FACTOR",
    "THRESHOLD_SCALED",
    "ProvenanceMerkleResult",
    "ZkBiometricProver",
    "build_provenance_merkle_tree",
    "canonicalize_json",
    "compute_commitment",
    "compute_scaled_dot_product",
    "dequantize_vector",
    "hash_face_embedding",
    "keccak256_bytes",
    "keccak256_hex",
    "quantize_vector",
    "sha256_bytes",
    "sha256_file",
    "verify_merkle_root",
    "verify_quantized_match",
]
