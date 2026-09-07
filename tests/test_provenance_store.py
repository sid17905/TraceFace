"""Test persistent storage for provenance graphs."""

import tempfile
from pathlib import Path

from src.pipeline.types import OriginNode, PropagationEdge
from src.storage.provenance_store import ProvenanceStore


def test_store_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        store = ProvenanceStore(db_path=Path(tmp) / "test.db")
        
        store.create_job("test-job-1", "test-scan-123", "running")
        
        node1 = OriginNode(
            node_id="node-1",
            platform="twitter",
            post_url="https://x.com/test/status/123",
            author_handle="@test",
            timestamp_utc="2026-01-01T00:00:00Z",
            phash="a1b2c3d4e5f6",
            similarity_score=0.92,
            laplacian_score=400.0,
            is_root_zero=True,
        )
        
        node2 = OriginNode(
            node_id="node-2",
            platform="reddit",
            post_url="https://reddit.com/r/test/comments/abc",
            author_handle="/r/test",
            timestamp_utc="2026-01-02T00:00:00Z",
            phash="a1b2c3d4e5f7",
            similarity_score=0.88,
            laplacian_score=350.0,
        )
        
        store.save_node(node1, "test-job-1")
        store.save_node(node2, "test-job-1")
        
        edge = PropagationEdge(
            source_id="node-1",
            target_id="node-2",
            delta_seconds=86400.0,
            phash_hamming_distance=2,
            degradation_score=0.05,
        )
        store.save_edge(edge, "test-job-1")
        
        graph = store.load_graph_by_job("test-job-1")
        
        assert graph is not None
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.root_zero_node_id == "node-1"
        
        assert graph.nodes[0].platform == "twitter"
        assert graph.nodes[1].platform == "reddit"
        assert graph.edges[0].source_id == "node-1"
        assert graph.edges[0].phash_hamming_distance == 2


def test_find_similar_by_phash():
    with tempfile.TemporaryDirectory() as tmp:
        store = ProvenanceStore(db_path=Path(tmp) / "test.db")
        
        store.create_job("test-job-2", "test-scan-456", "running")
        
        node1 = OriginNode(
            node_id="node-a",
            platform="twitter",
            post_url="https://x.com/test1/status/1",
            phash="a1b2c3d4e5f6",
            similarity_score=0.9,
            laplacian_score=400.0,
        )
        
        node2 = OriginNode(
            node_id="node-b",
            platform="reddit",
            post_url="https://reddit.com/r/test/comments/2",
            phash="a1b2c3d4e5f7",
            similarity_score=0.85,
            laplacian_score=380.0,
        )
        
        node3 = OriginNode(
            node_id="node-c",
            platform="instagram",
            post_url="https://instagram.com/p/abc",
            phash="ffffffffffff",
            similarity_score=0.7,
            laplacian_score=300.0,
        )
        
        store.save_node(node1, "test-job-2")
        store.save_node(node2, "test-job-2")
        store.save_node(node3, "test-job-2")
        
        similar = store.find_similar_nodes_by_phash("a1b2c3d4e5f6", max_hamming=2)
        
        assert len(similar) == 2
        assert any(n.node_id == "node-a" for n in similar)
        assert any(n.node_id == "node-b" for n in similar)
        assert not any(n.node_id == "node-c" for n in similar)


if __name__ == "__main__":
    test_store_roundtrip()
    print("✓ Roundtrip test passed")
    test_find_similar_by_phash()
    print("✓ Similar phash search test passed")
    print("All storage tests passed!")
