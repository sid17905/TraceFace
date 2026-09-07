"""Temporal origin DAG router.

Reconstructs the propagation graph of a piece of media across platforms from a
set of candidate origin nodes, identifying the earliest "Root-Zero" publisher
and annotating each hop with time delta, pHash Hamming distance, and perceptual
degradation. Pure computation — no models or network required.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from api.schemas.graph import GraphPropagateRequest, GraphPropagateResponse

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post(
    "/propagate",
    response_model=GraphPropagateResponse,
    summary="Reconstruct the temporal origin DAG and identify Root-Zero",
)
async def propagate(req: GraphPropagateRequest) -> GraphPropagateResponse:
    from src.analytics.origin_graph import build_propagation_graph

    graph = await run_in_threadpool(
        build_propagation_graph, req.nodes, req.max_hamming_distance
    )

    mermaid = None
    if req.include_mermaid:
        from src.analytics.graph_visualizer import render_mermaid_graph

        mermaid = render_mermaid_graph(graph)

    return GraphPropagateResponse(graph=graph, mermaid=mermaid)


@router.get(
    "/jobs",
    summary="List all stored provenance graphs",
)
async def list_stored_graphs() -> dict:
    from src.storage.provenance_store import get_provenance_store
    import sqlite3
    from datetime import datetime
    
    store = get_provenance_store()
    
    # Query all jobs with node/edge counts
    conn = sqlite3.connect(store.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            j.job_id,
            j.scan_id,
            j.status,
            j.created_at,
            COUNT(DISTINCT n.node_id) as nodes_count,
            COUNT(DISTINCT e.id) as edges_count
        FROM scan_jobs j
        LEFT JOIN origin_nodes n ON n.job_id = j.job_id
        LEFT JOIN propagation_edges e ON e.job_id = j.job_id
        GROUP BY j.job_id
        ORDER BY j.created_at DESC
    """)
    
    jobs = []
    for row in cursor.fetchall():
        jobs.append({
            "job_id": row[0],
            "scan_id": row[1],
            "status": row[2],
            "created_at": row[3],
            "nodes_count": row[4] or 0,
            "edges_count": row[5] or 0,
        })
    
    conn.close()
    
    return {
        "jobs": jobs,
        "total": len(jobs),
    }


@router.get(
    "/job/{job_id}",
    summary="Load a persisted provenance graph by job ID",
)
async def get_job_graph(job_id: str) -> dict:
    from src.storage.provenance_store import get_provenance_store
    
    store = get_provenance_store()
    graph = store.load_graph_by_job(job_id)
    
    if graph is None:
        raise HTTPException(status_code=404, detail=f"No graph found for job_id: {job_id}")
    
    return {
        "job_id": job_id,
        "graph": graph.model_dump(),
        "nodes_count": len(graph.nodes),
        "edges_count": len(graph.edges),
    }


@router.get(
    "/similar/{phash}",
    summary="Find graph nodes with similar perceptual hashes",
)
async def find_similar_nodes(phash: str, max_hamming: int = 12) -> dict:
    from src.storage.provenance_store import get_provenance_store
    
    store = get_provenance_store()
    nodes = store.find_similar_nodes_by_phash(phash, max_hamming)
    
    return {
        "query_phash": phash,
        "max_hamming_distance": max_hamming,
        "matching_nodes": [n.model_dump() for n in nodes],
        "count": len(nodes),
    }


@router.get(
    "/visualize/{job_id}",
    summary="Get graph visualization data in D3.js format",
)
async def get_graph_visualization(job_id: str) -> dict:
    from src.storage.provenance_store import get_provenance_store
    from src.analytics.graph_visualizer import to_d3_format
    
    store = get_provenance_store()
    graph = store.load_graph_by_job(job_id)
    
    if graph is None:
        raise HTTPException(status_code=404, detail=f"No graph found for job_id: {job_id}")
    
    return to_d3_format(graph)


@router.get(
    "/visualize/{job_id}/cytoscape",
    summary="Get graph visualization data in Cytoscape.js format",
)
async def get_graph_cytoscape(job_id: str) -> dict:
    from src.storage.provenance_store import get_provenance_store
    from src.analytics.graph_visualizer import to_cytoscape_format
    
    store = get_provenance_store()
    graph = store.load_graph_by_job(job_id)
    
    if graph is None:
        raise HTTPException(status_code=404, detail=f"No graph found for job_id: {job_id}")
    
    return to_cytoscape_format(graph)
