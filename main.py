"""Run the AeroDrift scan using local mock data."""

import time

from rich.console import Console

from aws_data import load_mock_resources
from dashboard import display_dashboard
from database import (
    get_latest_topology_diff,
    save_scan_result,
    save_topology_snapshot,
    summarize_topology_diff,
)
from drift_detector import detect_security_drift
from graph_engine import apply_mock_security_group_drift, build_topology
from remediation import (
    RemediationInput,
    generate_recommendations,
    generate_remediation_code,
    validate_remediation_code,
)


def run_scan() -> None:
    """Load resources, analyze the topology, display findings, and save a result."""
    console = Console()

    console.print("[bold cyan]Loading mock AWS resources...[/bold cyan]")
    mock_resources = load_mock_resources()

    console.print("[bold cyan]Building cloud topology graph...[/bold cyan]")
    cloud_topology = build_topology(mock_resources)
    snapshot_id = save_topology_snapshot(cloud_topology)
    console.print(
        f"[bold green]Topology snapshot saved: {snapshot_id}[/bold green]"
    )
    topology_diff = get_latest_topology_diff()
    if topology_diff["status"] == "NO HISTORY":
        console.print("[bold yellow]Historical topology comparison: NO HISTORY[/bold yellow]")
    elif topology_diff["status"] == "NO CHANGE":
        console.print("[bold green]Historical topology comparison: NO TOPOLOGY CHANGE[/bold green]")
    else:
        console.print(
            "[bold yellow]Historical topology comparison: "
            f"{summarize_topology_diff(topology_diff['previous_snapshot_id'], topology_diff['latest_snapshot_id'])}[/bold yellow]"
        )

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
        affected_resource_types = list(
            dict.fromkeys(
                cloud_topology.nodes[resource_id].get("resource_type", "Resource")
                for resource_id in drift_finding.path
            )
        )
        console.print(
            "[bold red]Affected resource summary: "
            f"{len(drift_finding.path)} total; types: "
            f"{', '.join(affected_resource_types)}[/bold red]"
        )
        console.print(
            f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
        )
        remediation_input = RemediationInput(
            security_group_id=drift_finding.affected_security_group or "",
            source_cidr=drift_finding.security_group_rule or "",
            protocol="tcp",
            from_port=80,
            to_port=80,
            reason="Revoke the unsafe public security-group ingress rule.",
        )
        remediation_source = generate_remediation_code(remediation_input)
        is_remediation_valid, remediation_message = validate_remediation_code(
            remediation_source
        )
        if is_remediation_valid:
            console.print(
                "[bold green]Generated remediation code passed AST validation "
                "and is ready for controlled execution.[/bold green]"
            )
        else:
            console.print(f"[bold red]{remediation_message}[/bold red]")
    else:
        console.print("[bold green]Audit status: SAFE[/bold green]")
        console.print(
            "[bold green]No Internet-to-Database path detected.[/bold green]"
        )
        console.print(
            f"[bold cyan]Detection time: {detection_elapsed_ms:.3f} ms[/bold cyan]"
        )
    remediation_recommendations = generate_recommendations(drift_finding)

    display_dashboard(
        cloud_topology,
        drift_finding,
        remediation_recommendations,
        topology_diff,
    )
    save_scan_result(drift_finding.status, remediation_recommendations)
    console.print("[bold green]Scan result saved to data/scan_results.db[/bold green]")


if __name__ == "__main__":
    run_scan()
