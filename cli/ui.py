"""
CLI Visualizer Module

This module provides a rich text user interface for rendering biometric
scan results directly in the terminal. It relies on the `rich` Python library
to draw tables, panels, and confidence gauges.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from src.pipeline.types import FaceScanOutput

console = Console()


def print_scan_results(output: FaceScanOutput):
    """
    Renders a beautiful CLI visualization of the biometric scan output.

    Args:
        output (FaceScanOutput): The complete scan data model to render.
    """
    # Create the main table for metadata
    meta_table = Table(show_header=False, box=None, padding=(0, 2))
    meta_table.add_row("[cyan]Scan ID[/cyan]", output.scan_id)
    meta_table.add_row("[cyan]Timestamp[/cyan]", output.timestamp_utc)
    meta_table.add_row("[cyan]Source File[/cyan]", output.source_image_path)

    # Create a table for Hashes
    hash_table = Table(
        title="[bold bright_magenta]Cryptographic Hashes",
        show_header=True,
        header_style="bold magenta",
    )
    hash_table.add_column("Algorithm", style="cyan")
    hash_table.add_column("Digest", style="green")

    hash_table.add_row("SHA-256", output.image_hash_sha256[:32] + "...")
    hash_table.add_row("Keccak-256", output.embedding_hash_keccak256[:32] + "...")
    hash_table.add_row("pHash", output.perceptual_hash_phash)

    # Create a table for Bounding Box
    bbox = output.bounding_box
    bbox_str = (
        f"[{int(bbox.x_min)}, {int(bbox.y_min)}, {int(bbox.x_max)}, {int(bbox.y_max)}]"
    )

    metrics_table = Table(title="[bold yellow]Vision Metrics", show_header=False)
    metrics_table.add_row("Bounding Box", f"[green]{bbox_str}[/green]")
    metrics_table.add_row(
        "Laplacian Score", f"{output.quality_metrics.laplacian_blur_score:.2f}"
    )
    metrics_table.add_row(
        "Blurry?",
        "[red]YES[/red]" if output.quality_metrics.is_blurry else "[green]NO[/green]",
    )

    is_fake = output.quality_metrics.is_deepfake
    fake_str = (
        "[bold red]YES (SYNTHETIC)[/bold red]"
        if is_fake
        else "[green]NO (HUMAN)[/green]"
    )
    metrics_table.add_row(
        "Liveness Check",
        f"{fake_str} (Score: {output.quality_metrics.deepfake_score:.2f})",
    )

    # Create confidence bar
    conf_pct = output.quality_metrics.confidence_score * 100
    color = "green" if conf_pct >= 68 else "red"

    conf_text = Text()
    conf_text.append("\nDetection Confidence: ", style="bold white")

    # We use rich.progress to manually render a single bar
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40, style="grey37", complete_style=color),
        TextColumn(f"[{color}]{conf_pct:.2f}%"),
        console=console,
    )
    task_id = progress.add_task("", total=100)
    progress.update(task_id, completed=conf_pct)

    # Render everything in a beautiful Panel
    from rich.console import Group

    group = Group(meta_table, "", hash_table, "", metrics_table, "", progress)

    console.print(
        Panel(
            group,
            title="[bold bright_green]TraceFace Biometric Scan Complete[/bold bright_green]",
            expand=False,
            border_style="bright_green",
        )
    )

def print_phase_header(title: str) -> None:
    console.print(f"\n[bold magenta][*] {title}[/bold magenta]")

def print_success(msg: str) -> None:
    console.print(f"[bold green][OK][/bold green] {msg}")

def print_error(msg: str) -> None:
    console.print(f"[bold red][ERROR]:[/bold red] {msg}")

def simulate_radar_scan() -> None:
    import random
    import time
    chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    console.print("[dim]Initiating Biometric Deep Scan...[/dim]")
    for _ in range(15):
        char = random.choice(chars)
        console.print(f"[cyan]{char} scanning biometric mesh...[/cyan]", end="\r")
        time.sleep(0.05)
    console.print(" " * 40, end="\r")

def print_evidence_table(candidates: list[Any]) -> None:
    table = Table(title="[bold magenta]OSINT Evidence Log", show_header=True)
    table.add_column("Platform", style="dim")
    table.add_column("Source URL", style="blue")
    
    for cand in candidates:
        platform = getattr(cand, "platform", "Web")
        url = getattr(cand, "post_url", getattr(cand, "source_url", "Unknown"))
        table.add_row(platform, url)
    console.print(table)

def print_verification_result(is_valid: bool, reason: str = "") -> None:
    from rich.align import Align
    if is_valid:
        panel = Panel(
            Text("Zero-Tamper Verified\nThe hash on Ethereum exactly matches the IPFS payload.", justify="center", style="bold green"),
            title="[bold green]CRYPTOGRAPHIC AUDIT PASSED[/bold green]",
            expand=False
        )
    else:
        panel = Panel(
            Text(f"Tamper Detected!\n{reason}", justify="center", style="bold red"),
            title="[bold red]CRYPTOGRAPHIC AUDIT FAILED[/bold red]",
            expand=False
        )
    console.print(Align.center(panel))


def print_propagation_dag(graph: Any) -> None:
    from src.analytics.graph_visualizer import build_rich_tree
    tree = build_rich_tree(graph)
    console.print(
        Panel(
            tree,
            title="[bold cyan]Temporal Origin & Propagation Graph (Root-Zero DAG)[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )


def print_propagation_ascii(graph: Any) -> None:
    from src.analytics.graph_visualizer import render_ascii_timeline
    console.print(
        Panel(
            render_ascii_timeline(graph),
            title="[bold cyan]ASCII Timeline Waterfall (Root-Zero DAG)[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )


def print_zk_verification_result(zk_result: dict[str, Any]) -> None:
    is_valid = zk_result.get("is_valid_match", False)
    sim = zk_result.get("cosine_similarity", 0.0)
    thresh = zk_result.get("threshold_enforced", 0.68)
    q_commit = zk_result.get("query_commitment", "")
    l_commit = zk_result.get("ledger_commitment", "")

    table = Table(title="[bold yellow]Zero-Knowledge Biometric SNARK Proof", show_header=False)
    table.add_row("Proof Protocol", "[cyan]Groth16 (BN128)[/cyan]")
    table.add_row("Public Match Signal", "[green]1 (VERIFIED)[/green]" if is_valid else "[red]0 (REJECTED)[/red]")
    table.add_row("Proved Similarity", f"[bold green]{sim:.4f}[/bold green] (Threshold >= {thresh})")
    table.add_row("Query Commitment", f"[dim]{q_commit}[/dim]")
    table.add_row("Ledger Commitment", f"[dim]{l_commit}[/dim]")
    table.add_row("Privacy Guarantee", "[green]Zero float embeddings revealed on-chain[/green]")

    status_color = "green" if is_valid else "red"
    title = "[bold bright_green]zk-SNARK Biometric Proof Verified[/bold bright_green]" if is_valid else "[bold red]zk-SNARK Proof Verification Failed[/bold red]"
    console.print(Panel(table, title=title, border_style=status_color, expand=False))


def print_dispute_status(status_badge: str, record_hash: str, dispute_info: dict[str, Any] | None = None) -> None:
    table = Table(title="[bold magenta]On-Chain Provenance & Dispute Status", show_header=False)
    table.add_row("Record Hash", f"[dim]{record_hash}[/dim]")
    table.add_row("Current Status", f"[bold]{status_badge}[/bold]")
    if dispute_info:
        table.add_row("Claimant", f"[cyan]{dispute_info.get('claimant', 'Unknown')}[/cyan]")
        table.add_row("Reason Code", str(dispute_info.get("reason_code", "N/A")))
        table.add_row("Evidence CID", f"[dim]{dispute_info.get('evidence_cid', '')}[/dim]")
        table.add_row("Resolved?", "[green]YES[/green]" if dispute_info.get("resolved") else "[yellow]PENDING REVIEW[/yellow]")
    console.print(Panel(table, title="[bold magenta]Ledger Dispute Audit[/bold magenta]", border_style="magenta", expand=False))


def print_takedown_receipt(receipt: dict[str, Any]) -> None:
    table = Table(title="[bold bright_red]EIP-712 Decentralized Takedown Notice Filed", show_header=False)
    table.add_row("Status", f"[bold green]{receipt.get('status', 'submitted').upper()}[/bold green]")
    table.add_row("TX Hash", f"[yellow]{receipt.get('tx_hash', 'N/A')}[/yellow]")
    table.add_row("Record Hash", f"[dim]{receipt.get('record_hash', '')}[/dim]")
    table.add_row("Claimant", f"[cyan]{receipt.get('claimant', '')}[/cyan]")
    table.add_row("Reason Code", str(receipt.get("reason_code", "")))
    table.add_row("Evidence CID", f"[dim]{receipt.get('evidence_cid', '')}[/dim]")
    console.print(Panel(table, title="[bold red]Takedown Claim Successfully Anchored[/bold red]", border_style="red", expand=False))
