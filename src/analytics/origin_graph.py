from __future__ import annotations

from datetime import datetime, timezone

import networkx as nx

from src.analytics.degradation import calculate_degradation, hamming_distance_phash
from src.pipeline.types import OriginNode, PropagationEdge, PropagationGraph


def parse_timestamp_to_epoch(ts: str | float | None) -> float:
    if ts is None or ts == "":
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    clean_ts = str(ts).strip()
    try:
        return float(clean_ts)
    except ValueError:
        pass

    clean_iso = clean_ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
    ):
        try:
            dt = datetime.strptime(clean_ts, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            continue

    return 0.0


def build_propagation_graph(
    nodes: list[OriginNode],
    max_hamming_distance: int = 12,
) -> PropagationGraph:
    if not nodes:
        return PropagationGraph(nodes=[], edges=[], root_zero_node_id=None, total_hops=0)

    node_copies = [node.model_copy(deep=True) for node in nodes]

    node_timestamps = {
        n.node_id: parse_timestamp_to_epoch(n.timestamp_utc) for n in node_copies
    }

    sorted_nodes = sorted(
        node_copies,
        key=lambda n: (
            node_timestamps[n.node_id] if node_timestamps[n.node_id] > 0 else float("inf"),
            -float(n.laplacian_score),
            -float(n.similarity_score),
        ),
    )

    edges: list[PropagationEdge] = []
    dag = nx.DiGraph()
    for n in sorted_nodes:
        dag.add_node(n.node_id)

    for i, target_node in enumerate(sorted_nodes):
        if i == 0:
            continue

        target_time = node_timestamps[target_node.node_id]
        best_parent: OriginNode | None = None
        best_dist = max_hamming_distance + 1
        min_time_delta = float("inf")

        for j in range(i):
            src_node = sorted_nodes[j]
            src_time = node_timestamps[src_node.node_id]

            if src_time > target_time > 0:
                continue

            dist = hamming_distance_phash(src_node.phash, target_node.phash)
            if dist <= max_hamming_distance:
                time_delta = max(0.0, target_time - src_time) if (target_time > 0 and src_time > 0) else 0.0
                if dist < best_dist or (dist == best_dist and time_delta < min_time_delta):
                    best_parent = src_node
                    best_dist = dist
                    min_time_delta = time_delta

        if best_parent is None and i > 0:
            best_parent = sorted_nodes[0]
            best_dist = hamming_distance_phash(best_parent.phash, target_node.phash)
            min_time_delta = max(0.0, target_time - node_timestamps[best_parent.node_id])

        if best_parent is not None:
            deg_score = calculate_degradation(best_parent, target_node)
            edge = PropagationEdge(
                source_id=best_parent.node_id,
                target_id=target_node.node_id,
                delta_seconds=round(min_time_delta, 2),
                phash_hamming_distance=best_dist,
                degradation_score=deg_score,
            )
            edges.append(edge)
            dag.add_edge(best_parent.node_id, target_node.node_id)

    root_candidates = [n for n in sorted_nodes if dag.in_degree(n.node_id) == 0]
    if root_candidates:
        root_node = sorted(
            root_candidates,
            key=lambda n: (
                node_timestamps[n.node_id] if node_timestamps[n.node_id] > 0 else float("inf"),
                -float(n.laplacian_score),
            ),
        )[0]
    else:
        root_node = sorted_nodes[0]

    for n in sorted_nodes:
        n.is_root_zero = (n.node_id == root_node.node_id)

    try:
        if nx.is_directed_acyclic_graph(dag) and len(dag) > 0:
            total_hops = nx.dag_longest_path_length(dag)
        else:
            total_hops = len(edges)
    except Exception:
        total_hops = len(edges)

    return PropagationGraph(
        nodes=sorted_nodes,
        edges=edges,
        root_zero_node_id=root_node.node_id,
        total_hops=int(total_hops),
    )
