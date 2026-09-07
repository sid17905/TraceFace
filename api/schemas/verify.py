"""Schemas for the zero-tamper verification router."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VerifyResponse(BaseModel):
    """Result of auditing a provenance record against the chain + IPFS + Merkle root."""

    is_authentic: bool
    status: str = Field(..., description="AUTHENTIC | TAMPER_DETECTED | DISPUTED | REVOKED | NOT_FOUND_ON_CHAIN")
    status_badge: str
    record_hash: str
    on_chain_exists: bool
    on_chain_cid: str = ""
    on_chain_vector_hash: str = ""
    on_chain_timestamp: int = 0
    on_chain_registrant: str = ""
    recalculated_merkle_root: str = ""
    leaves_breakdown: dict[str, str] = Field(default_factory=dict)
    tamper_details: str | None = None
    social_metadata: dict[str, Any] | None = None
    biometric_similarity: float | None = None
    dispute_info: dict[str, Any] | None = None
