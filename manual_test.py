from src.pipeline.orchestrator import run_vision_pipeline
from cli.ui import print_scan_results

def run():
    print("[*] Running Orchestrator Vision Pipeline...")
    output = run_vision_pipeline("data/sample_inputs/sample_target.jpg")
    if output:
        print("\n[*] Rendered output using UI visualizer:\n")
        print_scan_results(output)

if __name__ == "__main__":
    run()
