import asyncio

import typer
from rich.console import Console

from cli import ui
from cli.verify import verify_hash
from main import run_integration_pipeline

app = typer.Typer(help="TraceFace CLI Engine: Biometric OSINT & Web3 Provenance")
console = Console()


@app.command()
def scan(
    image: str = typer.Option(..., "--image", "-i", help="Path to local target image"),
    url: str | None = typer.Option(None, "--url", "-u", help="Optional public URL for the same image (required for some OSINT engines)"),
) -> None:
    """Run the complete TraceFace biometric OSINT & provenance pipeline."""
    
    # We will use the rich console in main.py, but we can print a big banner here
    console.print("\n[bold cyan]=================================================[/bold cyan]")
    console.print("[bold cyan]            TraceFace CLI Engine                 [/bold cyan]")
    console.print("[bold cyan]=================================================[/bold cyan]\n")
    
    try:
        run_integration_pipeline(image, url)
    except Exception as e:  # noqa: BLE001
        console.print(f"\n[bold red]✘ FATAL ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def verify(
    tx_hash: str = typer.Option(..., "--hash", "-h", help="The Ethereum Transaction Hash to verify")
) -> None:
    """Cryptographically verify an existing TraceFace record from the blockchain."""
    
    console.print("\n[bold magenta]=================================================[/bold magenta]")
    console.print("[bold magenta]          TraceFace Cryptographic Audit          [/bold magenta]")
    console.print("[bold magenta]=================================================[/bold magenta]\n")
    
    try:
        is_valid, reason = asyncio.run(verify_hash(tx_hash))
        ui.print_verification_result(is_valid, reason)
    except Exception as e:  # noqa: BLE001
        console.print(f"\n[bold red]✘ VERIFICATION FAILED:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def demo() -> None:
    """Run an automated 1-click end-to-end demo."""
    import os
    
    demo_image = "/mnt/c/Users/shubham/Downloads/rock.jpg"
    demo_url = "https://upload.wikimedia.org/wikipedia/commons/1/1f/Dwayne_Johnson_2014_%28cropped%29.jpg"
    
    if not os.path.exists(demo_image):
        console.print(f"[bold red]✘ Demo image not found at {demo_image}[/bold red]")
        raise typer.Exit(code=1)
        
    console.print(f"[bold yellow]Running automated demo with {demo_image}...[/bold yellow]")
    scan(demo_image, demo_url)


if __name__ == "__main__":
    app()
