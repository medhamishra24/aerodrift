"""Run the AeroDrift scan using local mock data."""

import argparse

import networkx as nx

from rich.console import Console

from dashboard import display_dashboard
from database import (
    compare_topology_snapshots,
    get_topology_snapshot,
    save_scan_result,
    summarize_topology_diff,
)
from drift_detector import DriftFinding
from scan_service import run_scan_service


def run_scan() -> None:
    """Load resources, analyze the topology, display findings, and save a result."""
    console = Console()
    scan_result = run_scan_service(console)
    cloud_topology, drift_finding = _runtime_scan_objects(scan_result)
    topology_diff = scan_result["history"]
    remediation_recommendations = scan_result["drift"]["recommendations"]

    display_dashboard(
        cloud_topology,
        drift_finding,
        remediation_recommendations,
        topology_diff,
    )
    save_scan_result(drift_finding.status, remediation_recommendations)
    console.print("[bold green]Scan result saved to data/scan_results.db[/bold green]")


def _runtime_scan_objects(
    scan_result: dict[str, object],
) -> tuple[nx.DiGraph, DriftFinding]:
    """Rebuild presentation objects required by the unchanged Rich dashboard."""
    topology_result = scan_result["topology"]
    drift_result = scan_result["drift"]
    topology = nx.DiGraph()
    for node in topology_result["nodes"]:
        topology.add_node(
            node["id"],
            **{key: value for key, value in node.items() if key != "id"},
        )
    for edge in topology_result["edges"]:
        topology.add_edge(
            edge["source"],
            edge["target"],
            **{
                key: value
                for key, value in edge.items()
                if key not in {"source", "target"}
            },
        )
    security_group = drift_result["security_group"]
    finding = DriftFinding(
        internet_to_database_path=drift_result["internet_to_database_path"],
        status=drift_result["status"],
        message=drift_result["message"],
        path=tuple(drift_result["path"]),
        security_group_rule=security_group["rule"],
        affected_security_group=security_group["id"],
    )
    return topology, finding


def compare_snapshots_by_timestamp(
    first_timestamp: str,
    second_timestamp: str,
) -> None:
    """Display a historical topology comparison selected by timestamps."""
    console = Console()
    first_snapshot = get_topology_snapshot(timestamp=first_timestamp)
    second_snapshot = get_topology_snapshot(timestamp=second_timestamp)
    if first_snapshot is None or second_snapshot is None:
        console.print(
            "[bold yellow]Historical topology comparison: NO HISTORY[/bold yellow]"
        )
        return

    diff = compare_topology_snapshots(
        first_snapshot["snapshot_id"],
        second_snapshot["snapshot_id"],
    )
    if diff is None:
        console.print(
            "[bold yellow]Historical topology comparison: NO HISTORY[/bold yellow]"
        )
    elif not any(
        diff[key]
        for key in ("added_nodes", "removed_nodes", "added_edges", "removed_edges")
    ):
        console.print(
            "[bold green]Historical topology comparison: "
            "NO TOPOLOGY CHANGE[/bold green]"
        )
    else:
        console.print(
            "[bold yellow]Historical topology comparison: "
            f"{summarize_topology_diff(first_snapshot['snapshot_id'], second_snapshot['snapshot_id'])}"
            "[/bold yellow]"
        )


def _parse_arguments() -> argparse.Namespace:
    """Parse optional historical comparison CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the AeroDrift scan.")
    parser.add_argument(
        "--compare-timestamps",
        nargs=2,
        metavar=("FIRST_TIMESTAMP", "SECOND_TIMESTAMP"),
        help="Compare two saved topology snapshots by their timestamps.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_arguments()
    if arguments.compare_timestamps:
        compare_snapshots_by_timestamp(*arguments.compare_timestamps)
    else:
        run_scan()
