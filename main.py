"""Run the complete AeroDrift demonstration scan."""

from aws_data import load_mock_resources
from dashboard import display_dashboard
from database import save_scan_result
from drift_detector import detect_security_drift
from graph_engine import build_topology
from remediation import generate_recommendations


def run_scan() -> None:
    """Load resources, analyze topology, display findings, and save results."""
    print("Loading mock AWS resources...")
    resources = load_mock_resources()

    print("Building cloud topology graph...")
    topology = build_topology(resources)

    print("Checking for security drift...")
    finding = detect_security_drift(topology)
    recommendations = generate_recommendations(finding)

    display_dashboard(topology, finding, recommendations)
    save_scan_result(finding.status, recommendations)
    print("Scan result saved to data/scan_results.db")


if __name__ == "__main__":
    run_scan()
