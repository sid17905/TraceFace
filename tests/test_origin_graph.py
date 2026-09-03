from src.analytics.degradation import calculate_degradation, hamming_distance_phash
from src.analytics.graph_visualizer import render_ascii_timeline, render_mermaid_graph
from src.analytics.origin_graph import build_propagation_graph, parse_timestamp_to_epoch
from src.pipeline.types import OriginNode


def test_hamming_distance_phash():
    assert hamming_distance_phash("ffffffffffffffff", "ffffffffffffffff") == 0
    assert hamming_distance_phash("0x0000000000000000", "0x0000000000000001") == 1
    assert hamming_distance_phash("ffffffffffffffff", "0000000000000000") == 64
    assert hamming_distance_phash("", "abc") == 0


def test_calculate_degradation():
    node1 = OriginNode(
        node_id="n1",
        platform="Twitter/X",
        post_url="https://x.com/1",
        phash="0000000000000000",
        laplacian_score=150.0,
    )
    node2 = OriginNode(
        node_id="n2",
        platform="Reddit",
        post_url="https://reddit.com/1",
        phash="0000000000000003",
        laplacian_score=120.0,
    )
    deg = calculate_degradation(node1, node2)
    assert 0.0 <= deg <= 1.0
    assert deg > 0.0


def test_origin_graph_root_zero_resolution():
    nodes = [
        OriginNode(
            node_id="node_reddit",
            platform="Reddit",
            post_url="https://reddit.com/r/tech/1",
            author_handle="/r/technology",
            timestamp_utc="2026-04-18T14:42:00Z",
            phash="ffff0000ffff0003",
            laplacian_score=80.0,
        ),
        OriginNode(
            node_id="node_twitter",
            platform="Twitter/X",
            post_url="https://x.com/creator/1",
            author_handle="@creator",
            timestamp_utc="2026-04-18T10:30:00Z",
            phash="ffff0000ffff0000",
            laplacian_score=145.0,
        ),
        OriginNode(
            node_id="node_insta",
            platform="Instagram",
            post_url="https://instagram.com/p/1",
            author_handle="@repost_hub",
            timestamp_utc="2026-04-19T05:06:00Z",
            phash="ffff0000ffff0007",
            laplacian_score=60.0,
        ),
    ]

    graph = build_propagation_graph(nodes)
    assert graph.root_zero_node_id == "node_twitter"
    assert graph.nodes[0].is_root_zero is True
    assert len(graph.edges) == 2

    ascii_out = render_ascii_timeline(graph)
    assert "[Origin Root-Zero]" in ascii_out
    assert "Twitter/X (@creator)" in ascii_out
    assert "Reddit (/r/technology)" in ascii_out
    assert "Instagram (@repost_hub)" in ascii_out

    mermaid_out = render_mermaid_graph(graph)
    assert "graph TD" in mermaid_out
    assert "node_twitter" in mermaid_out


def test_origin_graph_empty_and_single():
    empty_graph = build_propagation_graph([])
    assert empty_graph.root_zero_node_id is None
    assert len(empty_graph.edges) == 0

    single_node = [
        OriginNode(
            node_id="single",
            platform="Twitter/X",
            post_url="https://x.com/s",
            phash="abcd",
        )
    ]
    graph = build_propagation_graph(single_node)
    assert graph.root_zero_node_id == "single"
    assert graph.nodes[0].is_root_zero is True
    assert len(graph.edges) == 0


def test_parse_timestamp_to_epoch():
    epoch = parse_timestamp_to_epoch("2026-04-18T10:30:00Z")
    assert epoch > 0
    assert parse_timestamp_to_epoch(None) == 0.0
    assert parse_timestamp_to_epoch("") == 0.0
