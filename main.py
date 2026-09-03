"""Run the AeroDrift scan using local mock data."""

import time

from rich.console import Console

from aws_data import load_mock_resources
from dashboard import display_dashboard
from database import save_scan_result
from drift_detector import detect_security_drift
from graph_engine import apply_mock_security_group_drift, build_topology
from remediation import generate_recommendations


def run_scan() -> None:
    """Load resources, analyze the topology, display findings, and save a result."""
    console = Console()

    console.print("[bold cyan]Loading mock AWS resources...[/bold cyan]")
    mock_resources = load_mock_resources()

    console.print("[bold cyan]Building cloud topology graph...[/bold cyan]")
    cloud_topology = build_topology(mock_resources)

    console.print("[bold cyan]Testing mock security-group drift...[/bold cyan]")
    cloud_topology.remove_edge("sg-public", "web-server")
    restricted_finding = detect_security_drift(cloud_topology)
    console.print(
        f"Restricted topology: {restricted_finding.status}"
    )
    apply_mock_security_group_drift(cloud_topology)
    security_group_rule = cloud_topology.edges["sg-public", "web-server"][
        "security_group_rule"
    ]
    console.print(
        f"Mock security-group rule changed to: {security_group_rule}"
    )

    console.print("[bold cyan]Checking for security drift...[/bold cyan]")
    detection_started_at = time.perf_counter()
    drift_finding = detect_security_drift(cloud_topology)
    detection_elapsed_ms = (time.perf_counter() - detection_started_at) * 1000
    if detection_elapsed_ms < 5000:
        console.print(
            "[bold green]Audit target passed: detection completed under 5 seconds.[/bold green]"
        )
    else:
        console.print(
            "[bold yellow]Audit target warning: detection took 5 seconds or longer.[/bold yellow]"
        )
    if drift_finding.internet_to_database_path:
        detected_path = " -> ".join(
            str(cloud_topology.nodes[resource_id].get("name", resource_id))
            for resource_id in drift_finding.path
        )
        console.print("[bold red]Audit status: UNSAFE[/bold red]")
        console.print(f"[bold red]Detected Internet-to-Database path: {detected_path}[/bold red]")
        console.print(
            f"[bold red]Affected resources: {len(drift_finding.path)}[/bold red]"
        )
        console.print(
            f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
        )
    else:
        console.print("[bold green]Audit status: SAFE[/bold green]")
        console.print(
            "[bold green]No Internet-to-Database path detected.[/bold green]"
        )
        console.print(
            f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
        )
    remediation_recommendations = generate_recommendations(drift_finding)

    display_dashboard(cloud_topology, drift_finding, remediation_recommendations)
    save_scan_result(drift_finding.status, remediation_recommendations)
    console.print("[bold green]Scan result saved to data/scan_results.db[/bold green]")


if __name__ == "__main__":
    run_scan()
