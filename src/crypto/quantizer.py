from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

SCALE_FACTOR = 10_000
THRESHOLD_SCALED = 68_000_000


def quantize_vector(
    vec: Sequence[float],
    scale: int = SCALE_FACTOR,
) -> list[int]:
    return [round(float(x) * scale) for x in vec]


def dequantize_vector(
    int_vec: Sequence[int],
    scale: int = SCALE_FACTOR,
) -> list[float]:
    return [round(float(x) / scale, 6) for x in int_vec]


def compute_scaled_dot_product(
    vec_a: Sequence[int],
    vec_b: Sequence[int],
) -> int:
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimension mismatch: {len(vec_a)} != {len(vec_b)}")
    return sum(int(a) * int(b) for a, b in zip(vec_a, vec_b))


def verify_quantized_match(
    vec_a: Sequence[int],
    vec_b: Sequence[int],
    threshold: int = THRESHOLD_SCALED,
) -> bool:
    return compute_scaled_dot_product(vec_a, vec_b) >= threshold


def compute_commitment(
    int_vec: Sequence[int],
) -> str:
    payload = json.dumps(list(int_vec), separators=(",", ":")).encode()
    digest = hashlib.sha256(payload).hexdigest()
    return f"0x{digest}"
