"""Request/response schemas for the scan (ingestion) router."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.pipeline.types import FaceScanOutput


class ScanUrlRequest(BaseModel):
    """Trigger a scan against a remotely-hosted image instead of an upload."""

    image_url: str = Field(..., description="Public URL of the target image to fetch and analyze.")
    run_osint: bool = Field(
        True,
        description="Whether to launch the background OSINT + provenance sealing pipeline.",
    )


class ScanResponse(BaseModel):
    """Synchronous result of the biometric extraction stage.

    ``job_id`` identifies the background provenance pipeline (OSINT -> merkle ->
    IPFS -> blockchain) whose progress can be streamed from
    ``GET /api/v1/scan/stream/{job_id}``.
    """

    job_id: str = Field(..., description="Identifier for the streaming provenance job.")
    scan: FaceScanOutput = Field(..., description="Full biometric extraction output.")
    osint_started: bool = Field(
        ..., description="True when the background OSINT/sealing pipeline was launched."
    )


class ScanJobResult(BaseModel):
    """Terminal result of the background provenance pipeline for a job."""

    job_id: str
    status: str
    verified_match: dict | None = None
    merkle_root: str | None = None
    ipfs_cid: str | None = None
    tx_hash: str | None = None
    error: str | None = None
