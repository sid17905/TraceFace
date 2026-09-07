from __future__ import annotations

from typing import TYPE_CHECKING

from rich.tree import Tree

if TYPE_CHECKING:
    from src.pipeline.types import PropagationGraph


def format_time_delta(seconds: float) -> str:
    if seconds <= 0:
        return "0s"
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60.0
    if hours < 24:
        return f"+{hours:.1f} hrs"
    days = hours / 24.0
    return f"+{days:.1f} days"


def render_ascii_timeline(graph: PropagationGraph) -> str:
    if not graph.nodes:
        return "[Empty Propagation Graph]"

    node_map = {n.node_id: n for n in graph.nodes}
    root_id = graph.root_zero_node_id or (graph.nodes[0].node_id if graph.nodes else None)
    if not root_id or root_id not in node_map:
        return "[Invalid Graph: Root-Zero Not Found]"

    root = node_map[root_id]
    handle_part = f" ({root.author_handle})" if root.author_handle else ""
    ts_part = f" {root.timestamp_utc} -" if root.timestamp_utc else ""
    lines = [f"[Origin Root-Zero]{ts_part} {root.platform}{handle_part}"]

    children_edges = [e for e in graph.edges if e.source_id == root_id]
    other_edges = [e for e in graph.edges if e.source_id != root_id]

    all_edges_to_show = children_edges + other_edges
    for idx, edge in enumerate(all_edges_to_show):
        is_last = (idx == len(all_edges_to_show) - 1)
        branch = "└───" if is_last else "├───"

        target_node = node_map.get(edge.target_id)
        if not target_node:
            continue

        target_handle = f" ({target_node.author_handle})" if target_node.author_handle else ""
        target_info = f"{target_node.platform}{target_handle}"
        time_str = format_time_delta(edge.delta_seconds)

        lines.append("       |")
        lines.append(f"       {branch} ({time_str} | pHash d={edge.phash_hamming_distance}) --> {target_info}")

    return "\n".join(lines)


def build_rich_tree(graph: PropagationGraph) -> Tree:
    if not graph.nodes:
        return Tree("[bold yellow]Empty Propagation Graph[/bold yellow]")

    node_map = {n.node_id: n for n in graph.nodes}
    root_id = graph.root_zero_node_id or graph.nodes[0].node_id
    root = node_map[root_id]

    handle_part = f" [cyan]({root.author_handle})[/cyan]" if root.author_handle else ""
    ts_part = f" [dim]{root.timestamp_utc}[/dim] -" if root.timestamp_utc else ""
    root_label = f"[bold green]Origin Root-Zero[/bold green]{ts_part} [bold white]{root.platform}[/bold white]{handle_part}"
    tree = Tree(root_label)

    adj: dict[str, list] = {}
    for edge in graph.edges:
        adj.setdefault(edge.source_id, []).append(edge)

    def add_children(parent_tree: Tree, parent_id: str, visited: set[str]):
        for edge in adj.get(parent_id, []):
            if edge.target_id in visited:
                continue
            visited.add(edge.target_id)
            target = node_map.get(edge.target_id)
            if not target:
                continue
            t_handle = f" [cyan]({target.author_handle})[/cyan]" if target.author_handle else ""
            time_str = format_time_delta(edge.delta_seconds)
            edge_label = (
                f"[yellow]({time_str} | pHash d={edge.phash_hamming_distance} | deg={edge.degradation_score})[/yellow] "
                f"--> [bold white]{target.platform}[/bold white]{t_handle}"
            )
            child_branch = parent_tree.add(edge_label)
            add_children(child_branch, edge.target_id, visited)

    add_children(tree, root_id, {root_id})
    return tree


def render_mermaid_graph(graph: PropagationGraph) -> str:
    lines = ["graph TD"]

    for node in graph.nodes:
        clean_id = node.node_id.replace("-", "_").replace(":", "_").replace(".", "_")
        label_parts = [node.platform]
        if node.author_handle:
            label_parts.append(node.author_handle)
        if node.timestamp_utc:
            label_parts.append(node.timestamp_utc)
        if node.is_root_zero:
            label_parts.append("Root-Zero")
        label = "<br/>".join(label_parts)
        lines.append(f'    {clean_id}["{label}"]')

    for edge in graph.edges:
        src_clean = edge.source_id.replace("-", "_").replace(":", "_").replace(".", "_")
        dst_clean = edge.target_id.replace("-", "_").replace(":", "_").replace(".", "_")
        time_str = format_time_delta(edge.delta_seconds)
        edge_label = f"d={edge.phash_hamming_distance} ({time_str})"
        lines.append(f"    {src_clean} -->|{edge_label}| {dst_clean}")

    return "\n".join(lines)


def to_d3_format(graph: PropagationGraph) -> dict[str, Any]:
    """Convert propagation graph to D3.js force layout format."""
    from typing import Any
    
    nodes = []
    for node in graph.nodes:
        nodes.append({
            "id": node.node_id,
            "platform": node.platform,
            "post_url": node.post_url,
            "author": node.author_handle,
            "timestamp": node.timestamp_utc,
            "phash": node.phash,
            "similarity": node.similarity_score,
            "laplacian": node.laplacian_score,
            "is_root": node.is_root_zero,
            "label": f"{node.platform}\n{node.author_handle}",
        })
    
    links = []
    for edge in graph.edges:
        links.append({
            "source": edge.source_id,
            "target": edge.target_id,
            "delta_seconds": edge.delta_seconds,
            "hamming": edge.phash_hamming_distance,
            "degradation": edge.degradation_score,
        })
    
    return {
        "nodes": nodes,
        "links": links,
        "root_zero_id": graph.root_zero_node_id,
        "total_hops": graph.total_hops,
    }


def to_cytoscape_format(graph: PropagationGraph) -> dict[str, Any]:
    """Convert propagation graph to Cytoscape.js format."""
    from typing import Any
    
    elements = []
    
    for node in graph.nodes:
        elements.append({
            "data": {
                "id": node.node_id,
                "platform": node.platform,
                "author": node.author_handle,
                "url": node.post_url,
                "similarity": node.similarity_score,
                "is_root": node.is_root_zero,
            }
        })
    
    for edge in graph.edges:
        elements.append({
            "data": {
                "id": f"{edge.source_id}-{edge.target_id}",
                "source": edge.source_id,
                "target": edge.target_id,
                "delta": edge.delta_seconds,
                "hamming": edge.phash_hamming_distance,
            }
        })
    
    return {"elements": elements}


def to_vis_network_format(graph: PropagationGraph) -> dict[str, Any]:
    """Convert propagation graph to Vis.js Network format."""
    from typing import Any
    
    platform_colors = {
        "twitter": "#1DA1F2",
        "reddit": "#FF4500",
        "instagram": "#E4405F",
        "linkedin": "#0A66C2",
        "youtube": "#FF0000",
        "tiktok": "#000000",
        "facebook": "#1877F2",
    }
    
    nodes = []
    for node in graph.nodes:
        color = platform_colors.get(node.platform.lower(), "#808080")
        nodes.append({
            "id": node.node_id,
            "label": f"{node.platform}\n@{node.author_handle}",
            "color": color,
            "size": 25 if node.is_root_zero else 20,
            "font": {"size": 14, "color": "#ffffff"},
            "title": f"URL: {node.post_url}\nSimilarity: {node.similarity_score:.3f}",
        })
    
    edges = []
    for edge in graph.edges:
        edges.append({
            "from": edge.source_id,
            "to": edge.target_id,
            "label": f"{edge.delta_seconds:.0f}s",
            "arrows": "to",
            "color": {"color": "#888888"},
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
    }


__all__ = [
    "render_ascii_timeline",
    "render_mermaid_graph",
    "to_d3_format",
    "to_cytoscape_format",
    "to_vis_network_format",
]
