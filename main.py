"""Coordinate the complete AeroDrift demonstration scan.

This module is the command-line entry point for AeroDrift. It connects the
project's modules into one predictable workflow: load mock cloud resources,
build their directed topology, detect Internet-to-Database drift, generate
remediation guidance, render the results, and persist the scan in SQLite.

The workflow uses mock data only, so it can be run locally without AWS
credentials or access to a cloud account.
"""

from aws_data import load_mock_resources
from dashboard import display_dashboard
from database import save_scan_result
from drift_detector import detect_security_drift
from graph_engine import build_topology
from remediation import generate_recommendations


def run_scan() -> None:
    """Run one complete AeroDrift scan from collection through persistence.

    The function deliberately keeps orchestration in one place while each
    imported module owns a single responsibility. Its console messages mark
    the major stages of the scan for a beginner-friendly demonstration.
    """
    print("Loading mock AWS resources...")
    # Collection is local and deterministic; no cloud credentials are required.
    mock_resources = load_mock_resources()

    print("Building cloud topology graph...")
    # Convert resource records into the directed graph used by the detector.
    cloud_topology = build_topology(mock_resources)

    print("Checking for security drift...")
    # Analyze reachability first, then derive actions from the resulting finding.
    drift_finding = detect_security_drift(cloud_topology)
    remediation_recommendations = generate_recommendations(drift_finding)

    # Present and persist the same result so the operator and scan history agree.
    display_dashboard(cloud_topology, drift_finding, remediation_recommendations)
    save_scan_result(drift_finding.status, remediation_recommendations)
    print("Scan result saved to data/scan_results.db")


if __name__ == "__main__":
    run_scan()
