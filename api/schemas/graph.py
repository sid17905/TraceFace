"""Schemas for the temporal origin DAG router."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.pipeline.types import OriginNode, PropagationGraph


class GraphPropagateRequest(BaseModel):
    """Reconstruct a propagation DAG from candidate origin nodes."""

    nodes: list[OriginNode] = Field(
        ..., description="Candidate media nodes (platform, timestamp, pHash, laplacian score)."
    )
    max_hamming_distance: int = Field(
        12,
        ge=0,
        le=64,
        description="Maximum pHash Hamming distance for two nodes to be linked as a hop.",
    )
    include_mermaid: bool = Field(
        False, description="Also return a Mermaid.js graph definition string."
    )


class GraphPropagateResponse(BaseModel):
    graph: PropagationGraph
    mermaid: str | None = None
