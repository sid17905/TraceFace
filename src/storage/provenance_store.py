"""
Persistent storage layer for provenance graph nodes and edges.

Uses SQLite for lightweight, file-based persistence that survives server restarts.
Stores OriginNode instances, PropagationEdge connections, and scan metadata.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.pipeline.types import OriginNode, PropagationEdge, PropagationGraph


class ProvenanceStore:
    """SQLite-backed persistence for provenance graph data."""

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            cache_dir = Path(".cache")
            cache_dir.mkdir(exist_ok=True)
            db_path = cache_dir / "provenance.db"
        
        self.db_path = Path(db_path)
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_jobs (
                job_id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                result_json TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS origin_nodes (
                node_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                post_url TEXT NOT NULL,
                author_handle TEXT,
                timestamp_utc TEXT,
                phash TEXT,
                similarity_score REAL,
                laplacian_score REAL,
                is_root_zero INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES scan_jobs(job_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS propagation_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                delta_seconds REAL,
                phash_hamming_distance INTEGER,
                degradation_score REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES scan_jobs(job_id),
                FOREIGN KEY (source_id) REFERENCES origin_nodes(node_id),
                FOREIGN KEY (target_id) REFERENCES origin_nodes(node_id),
                UNIQUE(source_id, target_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_job ON origin_nodes(job_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_phash ON origin_nodes(phash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_job ON propagation_edges(job_id)
        """)
        
        conn.commit()
        conn.close()

    def create_job(self, job_id: str, scan_id: str, status: str = "pending") -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO scan_jobs (job_id, scan_id, status, created_at) VALUES (?, ?, ?, ?)",
            (job_id, scan_id, status, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        conn.close()

    def update_job_status(self, job_id: str, status: str, result_json: str | None = None) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        if result_json:
            cursor.execute(
                "UPDATE scan_jobs SET status = ?, result_json = ? WHERE job_id = ?",
                (status, result_json, job_id)
            )
        else:
            cursor.execute(
                "UPDATE scan_jobs SET status = ? WHERE job_id = ?",
                (status, job_id)
            )
        conn.commit()
        conn.close()

    def save_node(self, node: OriginNode, job_id: str) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO origin_nodes 
               (node_id, job_id, platform, post_url, author_handle, timestamp_utc, 
                phash, similarity_score, laplacian_score, is_root_zero, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node.node_id,
                job_id,
                node.platform,
                node.post_url,
                node.author_handle,
                node.timestamp_utc,
                node.phash,
                node.similarity_score,
                node.laplacian_score,
                1 if node.is_root_zero else 0,
                datetime.now(timezone.utc).isoformat(),
            )
        )
        conn.commit()
        conn.close()

    def save_edge(self, edge: PropagationEdge, job_id: str) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO propagation_edges 
               (job_id, source_id, target_id, delta_seconds, phash_hamming_distance, 
                degradation_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                job_id,
                edge.source_id,
                edge.target_id,
                edge.delta_seconds,
                edge.phash_hamming_distance,
                edge.degradation_score,
                datetime.now(timezone.utc).isoformat(),
            )
        )
        conn.commit()
        conn.close()

    def save_graph(self, graph: PropagationGraph, job_id: str) -> None:
        for node in graph.nodes:
            self.save_node(node, job_id)
        for edge in graph.edges:
            self.save_edge(edge, job_id)

    def load_nodes_by_job(self, job_id: str) -> list[OriginNode]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT node_id, platform, post_url, author_handle, timestamp_utc,
                      phash, similarity_score, laplacian_score, is_root_zero
               FROM origin_nodes WHERE job_id = ? ORDER BY created_at""",
            (job_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        nodes = []
        for row in rows:
            nodes.append(OriginNode(
                node_id=row[0],
                platform=row[1],
                post_url=row[2],
                author_handle=row[3] or "",
                timestamp_utc=row[4] or "",
                phash=row[5] or "",
                similarity_score=row[6] or 0.0,
                laplacian_score=row[7] or 0.0,
                is_root_zero=bool(row[8]),
            ))
        return nodes

    def load_edges_by_job(self, job_id: str) -> list[PropagationEdge]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT source_id, target_id, delta_seconds, phash_hamming_distance, degradation_score
               FROM propagation_edges WHERE job_id = ? ORDER BY created_at""",
            (job_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        edges = []
        for row in rows:
            edges.append(PropagationEdge(
                source_id=row[0],
                target_id=row[1],
                delta_seconds=row[2] or 0.0,
                phash_hamming_distance=row[3] or 0,
                degradation_score=row[4] or 0.0,
            ))
        return edges

    def load_graph_by_job(self, job_id: str) -> PropagationGraph | None:
        nodes = self.load_nodes_by_job(job_id)
        if not nodes:
            return None
        
        edges = self.load_edges_by_job(job_id)
        root_zero = next((n.node_id for n in nodes if n.is_root_zero), None)
        
        return PropagationGraph(
            nodes=nodes,
            edges=edges,
            root_zero_node_id=root_zero,
            total_hops=len(edges),
        )

    def find_similar_nodes_by_phash(self, phash: str, max_hamming: int = 12) -> list[OriginNode]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT node_id, phash FROM origin_nodes WHERE phash IS NOT NULL AND phash != ''")
        rows = cursor.fetchall()
        conn.close()
        
        def hamming_distance(h1: str, h2: str) -> int:
            return sum(c1 != c2 for c1, c2 in zip(h1, h2))
        
        matching_ids = [
            row[0] for row in rows
            if row[1] and hamming_distance(phash, row[1]) <= max_hamming
        ]
        
        nodes = []
        for nid in matching_ids:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT node_id, platform, post_url, author_handle, timestamp_utc,
                          phash, similarity_score, laplacian_score, is_root_zero
                   FROM origin_nodes WHERE node_id = ?""",
                (nid,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                nodes.append(OriginNode(
                    node_id=row[0],
                    platform=row[1],
                    post_url=row[2],
                    author_handle=row[3] or "",
                    timestamp_utc=row[4] or "",
                    phash=row[5] or "",
                    similarity_score=row[6] or 0.0,
                    laplacian_score=row[7] or 0.0,
                    is_root_zero=bool(row[8]),
                ))
        return nodes


_store_singleton: ProvenanceStore | None = None


def get_provenance_store() -> ProvenanceStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = ProvenanceStore()
    return _store_singleton


__all__ = ["ProvenanceStore", "get_provenance_store"]
