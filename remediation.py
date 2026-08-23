"""Remediation suggestions generated from drift findings."""

from drift_detector import DriftFinding


def generate_recommendations(finding: DriftFinding) -> list[str]:
    """Generate remediation guidance from a security drift finding.

    Args:
        finding: Result of the Internet-to-Database reachability check.

    Returns:
        An ordered list of recommendations. A drift finding returns concrete
        actions to reduce public exposure; a clean finding returns monitoring
        guidance.
    """
    database_is_reachable_from_internet = finding.internet_to_database_path

    if not database_is_reachable_from_internet:
        # Monitoring remains useful even when the currently scanned route is safe.
        return ["Continue monitoring network paths and security group changes."]

    # These actions address the exposed route at the access, network, and
    # architecture levels respectively.
    return [
        # Remove unrestricted inbound access at the security-group boundary.
        "Close the open security group to public inbound traffic.",
        # Limit any required public access to explicitly trusted sources.
        "Restrict public access to approved IP ranges or trusted services.",
        # Remove the route so the database is not reachable from the Internet.
        "Remove the unnecessary Internet-to-Database route.",
    ]
