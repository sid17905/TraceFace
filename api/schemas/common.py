"""Shared response envelopes and error schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Uniform error body returned by the API exception handlers."""

    detail: str = Field(..., description="Human-readable error message.")
    error_code: str | None = Field(
        None, description="Machine-readable code, e.g. ERR_SYNTHETIC_DEEPFAKE_DETECTED."
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "traceface-api"
    version: str
    vision_loaded: bool = Field(
        ..., description="Whether the InsightFace models are warm in memory."
    )
    blockchain_connected: bool = Field(
        ..., description="Whether an EVM node is reachable at the configured RPC URL."
    )
    contract_deployed: bool = Field(
        ..., description="Whether a provenance registry contract address is configured."
    )


class MessageResponse(BaseModel):
    message: str
    data: dict[str, Any] | None = None
