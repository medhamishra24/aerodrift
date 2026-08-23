"""Security drift checks for the cloud topology."""

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True)
class DriftFinding:
    """Result of checking a potentially risky route."""

    internet_to_database_path: bool
    status: str
    message: str


def detect_security_drift(topology: nx.DiGraph) -> DriftFinding:
    """Detect whether the Internet can reach the database through the graph."""
    path_exists = nx.has_path(topology, "internet", "database")

    if path_exists:
        return DriftFinding(
            internet_to_database_path=True,
            status="DRIFT DETECTED",
            message="WARNING: Security Drift Detected - Internet can reach Database",
        )

    return DriftFinding(
        internet_to_database_path=False,
        status="NO DRIFT",
        message="No Internet to Database path detected",
    )
