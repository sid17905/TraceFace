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
