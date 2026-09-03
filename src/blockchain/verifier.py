from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.blockchain.client import BlockchainClient
from src.crypto.merkle import build_provenance_merkle_tree
from src.storage.ipfs_client import IPFSClient


@dataclass
class VerificationResult:
    is_authentic: bool
    status: str
    record_hash: str
    on_chain_exists: bool
    on_chain_cid: str
    on_chain_vector_hash: str
    on_chain_timestamp: int
    on_chain_registrant: str
    recalculated_merkle_root: str
    leaves_breakdown: dict[str, str]
    tamper_details: str | None = None
    social_metadata: dict[str, Any] | None = None
    biometric_similarity: float | None = None
    status_badge: str = "[AUTH] AUTHENTIC"
    dispute_info: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_authentic": self.is_authentic,
            "status": self.status,
            "status_badge": self.status_badge,
            "record_hash": self.record_hash,
            "on_chain_exists": self.on_chain_exists,
            "on_chain_cid": self.on_chain_cid,
            "on_chain_vector_hash": self.on_chain_vector_hash,
            "on_chain_timestamp": self.on_chain_timestamp,
            "on_chain_registrant": self.on_chain_registrant,
            "recalculated_merkle_root": self.recalculated_merkle_root,
            "leaves_breakdown": self.leaves_breakdown,
            "tamper_details": self.tamper_details,
            "social_metadata": self.social_metadata,
            "biometric_similarity": self.biometric_similarity,
            "dispute_info": self.dispute_info,
        }


class ZeroTamperVerifier:
    def __init__(
        self,
        blockchain_client: BlockchainClient | None = None,
        ipfs_client: IPFSClient | None = None,
    ):
        self.chain = blockchain_client or BlockchainClient()
        self.ipfs = ipfs_client or IPFSClient()

    def verify_by_record_hash(
        self,
        record_hash: str,
        simulate_tamper: bool = False,
    ) -> VerificationResult:
        on_chain = self.chain.get_provenance(record_hash)
        if not on_chain["exists"]:
            return VerificationResult(
                is_authentic=False,
                status="NOT_FOUND_ON_CHAIN",
                status_badge="[NOT FOUND] NOT FOUND",
                record_hash=record_hash,
                on_chain_exists=False,
                on_chain_cid="",
                on_chain_vector_hash="",
                on_chain_timestamp=0,
                on_chain_registrant="",
                recalculated_merkle_root="",
                leaves_breakdown={},
                tamper_details="Record hash not found on the blockchain ledger.",
            )

        cid = on_chain["ipfs_cid"]
        payload = self.ipfs.fetch_json(cid)

        if simulate_tamper and "social_provenance" in payload:
            payload["social_provenance"]["post_text_sha256"] = "0x" + "0" * 64
            payload["social_provenance"]["author_handle"] = "@imposter_tampered"

        merkle_info = payload.get("cryptographic_merkle", {})
        leaf_source = merkle_info.get("leaf_source_image", "0x" + "0" * 64)
        leaf_embedding = merkle_info.get("leaf_face_embedding", "0x" + "0" * 64)
        leaf_social = merkle_info.get("leaf_social_post", "0x" + "0" * 64)
        leaf_target = merkle_info.get("leaf_target_media", "0x" + "0" * 64)

        if simulate_tamper:
            from src.crypto.hasher import keccak256_bytes

            leaf_social = keccak256_bytes(b"tampered_social_post_evidence")

        recalculated_tree = build_provenance_merkle_tree(
            leaf_source,
            leaf_embedding,
            leaf_social,
            leaf_target,
        )

        clean_on_chain_hash = record_hash.lower()
        clean_computed_root = recalculated_tree.merkle_root.lower()
        is_match = clean_on_chain_hash == clean_computed_root

        dispute_status_str = "ACTIVE"
        dispute_data = None
        if getattr(self.chain, "contract", None):
            try:
                b32_record = self.chain._format_bytes32(record_hash)
                status_enum = self.chain.contract.functions.getRecordStatus(b32_record).call()
                from src.blockchain.dispute_client import STATUS_MAP
                if isinstance(status_enum, int):
                    dispute_status_str = STATUS_MAP.get(status_enum, "ACTIVE")
                elif isinstance(status_enum, str) and status_enum.isdigit():
                    dispute_status_str = STATUS_MAP.get(int(status_enum), "ACTIVE")

                disp = self.chain.contract.functions.getDispute(b32_record).call()
                if (
                    isinstance(disp, (list, tuple))
                    and len(disp) >= 5
                    and isinstance(disp[0], str)
                    and disp[0] != "0x0000000000000000000000000000000000000000"
                ):
                    dispute_data = {
                        "claimant": str(disp[0]),
                        "reason_code": int(disp[1]) if isinstance(disp[1], int) else 0,
                        "evidence_cid": str(disp[2]),
                        "timestamp": int(disp[3]) if isinstance(disp[3], int) else 0,
                        "resolved": bool(disp[4]),
                    }
            except Exception:
                pass

        if not is_match:
            verdict_status = "TAMPER_DETECTED"
            badge = "[TAMPER] TAMPER DETECTED"
        elif dispute_status_str == "REVOKED":
            verdict_status = "REVOKED"
            badge = "[REVOKED] REVOKED (Takedown Executed)"
            is_match = False
        elif dispute_status_str == "DISPUTED":
            verdict_status = "DISPUTED"
            badge = "[DISPUTED] DISPUTED (Claim Filed)"
        else:
            verdict_status = "AUTHENTIC"
            badge = "[AUTH] AUTHENTIC"

        return VerificationResult(
            is_authentic=is_match,
            status=verdict_status,
            status_badge=badge,
            record_hash=record_hash,
            on_chain_exists=True,
            on_chain_cid=cid,
            on_chain_vector_hash=on_chain["face_vector_hash"],
            on_chain_timestamp=on_chain["timestamp"],
            on_chain_registrant=on_chain["registrant"],
            recalculated_merkle_root=recalculated_tree.merkle_root,
            leaves_breakdown=recalculated_tree.to_dict(),
            tamper_details=(
                None
                if is_match
                else (
                    "Dispute status: REVOKED"
                    if verdict_status == "REVOKED"
                    else f"Mismatch detected: Computed root ({recalculated_tree.merkle_root}) != Ledger hash ({record_hash})"
                )
            ),
            social_metadata=payload.get("social_provenance"),
            biometric_similarity=payload.get("biometric_evidence", {}).get("cosine_similarity"),
            dispute_info=dispute_data,
        )
