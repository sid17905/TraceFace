"""Schemas for the zero-knowledge biometric proof router."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ZkProveRequest(BaseModel):
    """Prove ``cosine(query, ledger) >= threshold`` without revealing the vectors."""

    query_vector: list[float] = Field(..., description="512-D ArcFace embedding of the query face.")
    ledger_vector: list[float] = Field(..., description="512-D ArcFace embedding of the ledger face.")
    threshold: float = Field(0.68, ge=-1.0, le=1.0, description="Cosine similarity threshold to prove.")


class ZkProveResponse(BaseModel):
    proof: dict[str, Any]
    publicSignals: list[str]
    is_valid_match: bool
    cosine_similarity: float
    threshold_enforced: float
    scaled_dot_product: int
    scaled_threshold: int
    query_commitment: str
    ledger_commitment: str


class ZkVerifyRequest(BaseModel):
    """Verify a previously generated Groth16 proof payload."""

    proof: dict[str, Any]
    publicSignals: list[str]


class ZkVerifyResponse(BaseModel):
    is_valid: bool
