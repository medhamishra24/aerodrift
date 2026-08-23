"""Remediation suggestions generated from drift findings."""

from drift_detector import DriftFinding


def generate_recommendations(finding: DriftFinding) -> list[str]:
    """Return practical recommendations for the detected security condition."""
    if not finding.internet_to_database_path:
        return ["Continue monitoring network paths and security group changes."]

    return [
        "Close the open security group to public inbound traffic.",
        "Restrict public access to approved IP ranges or trusted services.",
        "Remove the unnecessary Internet-to-Database route.",
    ]
