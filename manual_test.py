from src.pipeline.orchestrator import run_vision_pipeline
from cli.ui import print_scan_results

def run():
    try:
        output = run_vision_pipeline("data/sample_inputs/sample_target.avif")
        print("\n[*] Orchestrator finished successfully!")
        if output:
            print("\n[*] Rendered output using UI visualizer:\n")
            print_scan_results(output)
    except ValueError as e:
        from rich.console import Console
        console = Console()
        console.print(f"\n[bold red]Pipeline Aborted:[/bold red] {e}")

if __name__ == "__main__":
    run()
