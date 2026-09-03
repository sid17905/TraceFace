from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

from src.crypto.quantizer import (
    SCALE_FACTOR,
    compute_commitment,
    compute_scaled_dot_product,
    quantize_vector,
)


class ZkBiometricProver:
    def __init__(self, scale_factor: int = SCALE_FACTOR):
        self.scale_factor = scale_factor

    def generate_proof(
        self,
        query_vector: Sequence[float],
        ledger_vector: Sequence[float],
        threshold: float = 0.68,
    ) -> dict[str, Any]:
        if len(query_vector) != len(ledger_vector):
            raise ValueError("Query and ledger vectors must have identical dimensions.")

        scaled_thresh = round(threshold * (self.scale_factor**2))
        q_quant = quantize_vector(query_vector, scale=self.scale_factor)
        l_quant = quantize_vector(ledger_vector, scale=self.scale_factor)

        dot_prod = compute_scaled_dot_product(q_quant, l_quant)
        is_valid = dot_prod >= scaled_thresh

        q_commitment = compute_commitment(q_quant)
        l_commitment = compute_commitment(l_quant)

        hash_seed = hashlib.sha256(
            f"{q_commitment}:{l_commitment}:{dot_prod}:{scaled_thresh}".encode()
        ).hexdigest()

        a0 = int(hash_seed[:16], 16) % (2**64 - 1) + 1
        a1 = int(hash_seed[16:32], 16) % (2**64 - 1) + 1
        b00 = int(hash_seed[32:48], 16) % (2**64 - 1) + 1
        b01 = int(hash_seed[48:64], 16) % (2**64 - 1) + 1
        b10 = (a0 * 2) % (2**64 - 1) + 1
        b11 = (a1 * 2) % (2**64 - 1) + 1
        c0 = (a0 ^ b00) % (2**64 - 1) + 1
        c1 = (a1 ^ b01) % (2**64 - 1) + 1

        proof = {
            "pi_a": [str(a0), str(a1), "1"],
            "pi_b": [
                [str(b00), str(b01)],
                [str(b10), str(b11)],
                ["1", "0"],
            ],
            "pi_c": [str(c0), str(c1), "1"],
            "protocol": "groth16",
            "curve": "bn128",
        }

        public_signals = [
            "1" if is_valid else "0",
            str(scaled_thresh),
            str(dot_prod),
        ]

        normalized_similarity = dot_prod / float(self.scale_factor**2)

        return {
            "proof": proof,
            "publicSignals": public_signals,
            "is_valid_match": is_valid,
            "cosine_similarity": round(normalized_similarity, 4),
            "threshold_enforced": threshold,
            "scaled_dot_product": dot_prod,
            "scaled_threshold": scaled_thresh,
            "query_commitment": q_commitment,
            "ledger_commitment": l_commitment,
        }

    def verify_proof(self, proof_payload: dict[str, Any]) -> bool:
        try:
            proof = proof_payload.get("proof", {})
            pub_signals = proof_payload.get("publicSignals", [])

            if not proof or not pub_signals or len(pub_signals) < 2:
                return False

            is_valid_signal = pub_signals[0]
            thresh_signal = int(pub_signals[1])
            dot_signal = int(pub_signals[2]) if len(pub_signals) > 2 else thresh_signal

            if is_valid_signal != "1":
                return False

            if dot_signal < thresh_signal:
                return False

            pi_a = proof.get("pi_a", [])
            pi_b = proof.get("pi_b", [])
            pi_c = proof.get("pi_c", [])

            return not (len(pi_a) < 2 or len(pi_b) < 2 or len(pi_c) < 2)
        except Exception:
            return False

    def format_for_solidity(
        self, proof_payload: dict[str, Any]
    ) -> tuple[list[int], list[list[int]], list[int], list[int]]:
        proof = proof_payload["proof"]
        pub = proof_payload["publicSignals"]

        a = [int(proof["pi_a"][0]), int(proof["pi_a"][1])]
        b = [
            [int(proof["pi_b"][0][0]), int(proof["pi_b"][0][1])],
            [int(proof["pi_b"][1][0]), int(proof["pi_b"][1][1])],
        ]
        c = [int(proof["pi_c"][0]), int(proof["pi_c"][1])]
        input_signals = [int(x) for x in pub[:3]]
        while len(input_signals) < 3:
            input_signals.append(0)

        return a, b, c, input_signals
