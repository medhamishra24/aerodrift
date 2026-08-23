"""Security drift checks for the cloud topology."""

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True)
class DriftFinding:
    """Immutable result of the Internet-to-Database reachability check.

    Attributes:
        internet_to_database_path: Whether the graph contains a directed route
            from the public Internet to the database.
        status: Short status label used by the dashboard and database record.
        message: Human-readable explanation shown to the operator.
    """

    internet_to_database_path: bool
    status: str
    message: str


def detect_security_drift(topology: nx.DiGraph) -> DriftFinding:
    """Detect whether the Internet can reach the database through the graph.

    Args:
        topology: Directed NetworkX graph containing ``internet`` and
            ``database`` resource nodes.

    Returns:
        A :class:`DriftFinding` describing the reachability result. A reachable
        database is treated as security drift because the route exposes the
        data layer to a public entry point.
    """
    # NetworkX follows edge direction, so this tests whether traffic can flow
    # from the public entry point to the protected database resource.
    internet_to_database_path_exists = nx.has_path(topology, "internet", "database")

    if internet_to_database_path_exists:
        # Keep the warning text stable because it is displayed and persisted.
        return DriftFinding(
            internet_to_database_path=True,
            status="DRIFT DETECTED",
            message="WARNING: Security Drift Detected - Internet can reach Database",
        )

    # A missing path is the expected secure result for this specific check.
    return DriftFinding(
        internet_to_database_path=False,
        status="NO DRIFT",
        message="No Internet to Database path detected",
    )
