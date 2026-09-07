"""Zero-tamper verification router.

Audits a provenance record hash (or EVM tx hash) against the on-chain registry
and its IPFS payload, recomputing the 4-leaf Merkle root to prove the sealed
evidence has not been tampered with. Also supports registering new identity
provenance records onto the ledger.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from api.schemas.verify import VerifyResponse

router = APIRouter(prefix="/verify", tags=["verify"])


class RegisterIdentityRequest(BaseModel):
    record_hash: str = Field(..., description="Merkle root or canonical provenance hash.")
    ipfs_cid: str = Field(..., description="IPFS CID of the metadata bundle.")
    face_vector_hash: str = Field(..., description="Keccak-256 hash of the 512-D embedding.")
    owner_address: str | None = Field(None, description="Registrant Ethereum address.")
    metadata: dict[str, Any] | None = Field(None, description="Optional social/biometric metadata.")


@router.post(
    "/register",
    summary="Register a new person's biometric provenance record onto the blockchain ledger",
)
async def register_identity(req: RegisterIdentityRequest) -> dict[str, Any]:
    from src.blockchain.client import BlockchainClient

    def _register():
        client = BlockchainClient()
        if client.is_connected() and client.contract is not None:
            return client.register_provenance(
                record_hash=req.record_hash,
                ipfs_cid=req.ipfs_cid,
                face_vector_hash=req.face_vector_hash,
            )
        import hashlib
        import time

        return {
            "status": "success (simulated)",
            "tx_hash": "0x" + hashlib.sha256(f"{req.record_hash}:{time.time()}".encode()).hexdigest(),
            "record_hash": req.record_hash,
            "ipfs_cid": req.ipfs_cid,
            "registrant": req.owner_address or "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "timestamp": int(time.time()),
        }

    receipt = await run_in_threadpool(_register)
    return receipt


@router.get(
    "/{record_hash}",
    response_model=VerifyResponse,
    summary="Audit a provenance record's on-chain + Merkle integrity",
)
async def verify_record(
    record_hash: str,
    simulate_tamper: bool = Query(
        False, description="Inject a tampered leaf to demonstrate Merkle root collapse."
    ),
) -> VerifyResponse:
    from src.blockchain.verifier import ZeroTamperVerifier

    verifier = ZeroTamperVerifier()
    result = await run_in_threadpool(
        verifier.verify_by_record_hash, record_hash, simulate_tamper
    )
    return VerifyResponse(**result.to_dict())
