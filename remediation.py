"""Remediation suggestions generated from drift findings."""

from drift_detector import DriftFinding


def generate_recommendations(finding: DriftFinding) -> list[str]:
    """Generate remediation guidance from a security drift finding.

    Args:
        finding: Result of the Internet-to-Database reachability check.

    Returns:
        An ordered list of recommendations for the detected security state.
    """
    public_database_path_exists: bool = finding.internet_to_database_path

    if not public_database_path_exists:
        return ["Continue monitoring network paths and security group changes."]

    return [
        "Close the open security group to public inbound traffic.",
        "Restrict public access to approved IP ranges or trusted services.",
        "Remove the unnecessary Internet-to-Database route.",
    ]
