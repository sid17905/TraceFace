from dataclasses import dataclass
from typing import Any, Dict, Optional
from src.blockchain.client import BlockchainClient
from src.storage.ipfs_client import IPFSClient
from src.crypto.merkle import build_provenance_merkle_tree


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
    leaves_breakdown: Dict[str, str]
    tamper_details: Optional[str] = None
    social_metadata: Optional[Dict[str, Any]] = None
    biometric_similarity: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_authentic": self.is_authentic,
            "status": self.status,
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
        }


class ZeroTamperVerifier:
    def __init__(
        self,
        blockchain_client: Optional[BlockchainClient] = None,
        ipfs_client: Optional[IPFSClient] = None,
    ):
        self.chain = blockchain_client or BlockchainClient()
        self.ipfs = ipfs_client or IPFSClient()

    def verify_by_record_hash(
        self,
        record_hash: str,
        simulate_tamper: bool = False
    ) -> VerificationResult:
        """
        Queries blockchain ledger, fetches IPFS payload, recalculates Merkle root,
        and verifies complete zero-tamper cryptographic integrity.
        """
        on_chain = self.chain.get_provenance(record_hash)
        if not on_chain["exists"]:
            return VerificationResult(
                is_authentic=False,
                status="NOT_FOUND_ON_CHAIN",
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

        # Simulation mode for hackathon demonstrations
        if simulate_tamper:
            if "social_provenance" in payload:
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

        is_match = (clean_on_chain_hash == clean_computed_root)

        return VerificationResult(
            is_authentic=is_match,
            status="AUTHENTIC" if is_match else "TAMPER_DETECTED",
            record_hash=record_hash,
            on_chain_exists=True,
            on_chain_cid=cid,
            on_chain_vector_hash=on_chain["face_vector_hash"],
            on_chain_timestamp=on_chain["timestamp"],
            on_chain_registrant=on_chain["registrant"],
            recalculated_merkle_root=recalculated_tree.merkle_root,
            leaves_breakdown=recalculated_tree.to_dict(),
            tamper_details=(
                None if is_match
                else f"Mismatch detected: Computed root ({recalculated_tree.merkle_root}) != Ledger hash ({record_hash})"
            ),
            social_metadata=payload.get("social_provenance"),
            biometric_similarity=payload.get("biometric_evidence", {}).get("cosine_similarity"),
        )
