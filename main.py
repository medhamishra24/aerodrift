"""Run the AeroDrift scan using local mock data."""

import time

from rich.console import Console

from aws_data import load_mock_resources
from dashboard import display_dashboard
from database import save_scan_result
from drift_detector import detect_security_drift
from graph_engine import build_topology
from remediation import generate_recommendations


def run_scan() -> None:
    """Load resources, analyze the topology, display findings, and save a result."""
    console = Console()

    console.print("[bold cyan]Loading mock AWS resources...[/bold cyan]")
    mock_resources = load_mock_resources()

    console.print("[bold cyan]Building cloud topology graph...[/bold cyan]")
    cloud_topology = build_topology(mock_resources)

    console.print("[bold cyan]Checking for security drift...[/bold cyan]")
    detection_started_at = time.perf_counter()
    drift_finding = detect_security_drift(cloud_topology)
    detection_elapsed_ms = (time.perf_counter() - detection_started_at) * 1000
    console.print(
        f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
    )
    remediation_recommendations = generate_recommendations(drift_finding)

    display_dashboard(cloud_topology, drift_finding, remediation_recommendations)
    save_scan_result(drift_finding.status, remediation_recommendations)
    console.print("[bold green]Scan result saved to data/scan_results.db[/bold green]")


if __name__ == "__main__":
    run_scan()
