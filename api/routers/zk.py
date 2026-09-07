"""Zero-knowledge biometric proof router.

Wraps the Groth16 biometric prover: proves that two 512-D ArcFace embeddings are
similar beyond a threshold (an authentic identity match) without revealing the
vectors themselves — only quantized commitments and the scaled dot product are
exposed in the public signals.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from api.dependencies import get_zk_prover
from api.schemas.zk import (
    ZkProveRequest,
    ZkProveResponse,
    ZkVerifyRequest,
    ZkVerifyResponse,
)

router = APIRouter(prefix="/zk", tags=["zk"])


@router.post(
    "/prove",
    response_model=ZkProveResponse,
    summary="Generate a Groth16 proof that two embeddings match above threshold",
)
async def prove(req: ZkProveRequest) -> ZkProveResponse:
    if len(req.query_vector) != len(req.ledger_vector):
        raise HTTPException(
            status_code=422,
            detail=f"Vector dimension mismatch: {len(req.query_vector)} != {len(req.ledger_vector)}",
        )

    prover = get_zk_prover()
    result = await run_in_threadpool(
        prover.generate_proof, req.query_vector, req.ledger_vector, req.threshold
    )
    return ZkProveResponse(**result)


@router.post(
    "/verify",
    response_model=ZkVerifyResponse,
    summary="Verify a Groth16 biometric proof payload",
)
async def verify(req: ZkVerifyRequest) -> ZkVerifyResponse:
    prover = get_zk_prover()
    payload = {"proof": req.proof, "publicSignals": req.publicSignals}
    is_valid = await run_in_threadpool(prover.verify_proof, payload)
    return ZkVerifyResponse(is_valid=is_valid)
