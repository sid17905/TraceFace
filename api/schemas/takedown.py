"""Schemas for the EIP-712 takedown / ownership-dispute router."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TypedDataRequest(BaseModel):
    """Build the EIP-712 typed payload a wallet will sign for a takedown claim."""

    record_hash: str = Field(..., description="bytes32 provenance record hash being disputed.")
    claimant: str = Field(..., description="Ethereum address claiming biometric ownership.")
    reason_code: int = Field(
        1, ge=1, le=255, description="1=Identity Theft, 2=Unauthorized Diffusion, 3=Deepfake Impersonation."
    )
    evidence_ipfs_cid: str = Field("", description="Optional IPFS CID with cryptographic evidence.")
    deadline: int | None = Field(
        None, description="Unix expiry for the signature. Defaults to now + 24h."
    )


class TypedDataResponse(BaseModel):
    """EIP-712 payload plus the resolved nonce/deadline/domain for wallet signing."""

    typed_data: dict[str, Any]
    nonce: int
    deadline: int
    chain_id: int
    verifying_contract: str


class TakedownSubmitRequest(BaseModel):
    """Submit a signed takedown.

    Provide EITHER a wallet ``signature`` over the typed data (preferred: the
    private key never leaves the browser) OR a server-side ``private_key`` to
    sign and relay. When no chain is connected the endpoint returns a simulated
    receipt so the UI flow works end-to-end offline.
    """

    record_hash: str
    reason_code: int = Field(1, ge=1, le=255)
    evidence_ipfs_cid: str = ""
    deadline: int | None = None
    claimant: str | None = Field(None, description="Required when submitting a wallet signature.")
    signature: str | None = Field(None, description="EIP-712 signature produced by the claimant wallet.")
    private_key: str | None = Field(
        None, description="Server-side signing key (dev only). Ignored if a signature is supplied."
    )


class TakedownReceipt(BaseModel):
    status: str
    tx_hash: str | None = None
    record_hash: str
    claimant: str
    reason_code: int
    evidence_cid: str
    new_record_status: str = "DISPUTED"
    block_number: int | None = None
    gas_used: int | None = None
    recovered_signer: str | None = None
    simulated: bool = False


class RecordStatusResponse(BaseModel):
    record_hash: str
    status: str
    dispute_info: dict[str, Any] | None = None
