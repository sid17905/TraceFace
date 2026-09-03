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
    console.print(f"[bold green]✔[/bold green] {msg}")

def print_error(msg: str) -> None:
    console.print(f"[bold red]✘ ERROR:[/bold red] {msg}")

def simulate_radar_scan() -> None:
    import time
    import random
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
