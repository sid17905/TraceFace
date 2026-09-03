from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.pipeline.types import OriginNode


def hamming_distance_phash(hash1: str, hash2: str) -> int:
    if not hash1 or not hash2:
        return 0
    clean1 = hash1.strip().lower().removeprefix("0x")
    clean2 = hash2.strip().lower().removeprefix("0x")
    if len(clean1) != len(clean2):
        max_len = max(len(clean1), len(clean2))
        clean1 = clean1.zfill(max_len)
        clean2 = clean2.zfill(max_len)
    try:
        val1 = int(clean1, 16)
        val2 = int(clean2, 16)
        return (val1 ^ val2).bit_count()
    except ValueError:
        return sum(c1 != c2 for c1, c2 in zip(clean1, clean2))


def calculate_degradation(source_node: OriginNode, target_node: OriginNode) -> float:
    phash_dist = hamming_distance_phash(source_node.phash, target_node.phash)
    lap1 = float(source_node.laplacian_score)
    lap2 = float(target_node.laplacian_score)

    if lap1 > 0:
        lap_decay = max(0.0, (lap1 - lap2) / lap1)
    else:
        lap_decay = 0.0

    score = (min(phash_dist, 64) / 64.0) * 0.6 + lap_decay * 0.4
    return round(float(min(1.0, max(0.0, score))), 4)
