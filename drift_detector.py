"""Security drift checks for the cloud topology."""

from dataclasses import dataclass
from typing import Literal, TypeAlias

import networkx as nx


DriftStatus: TypeAlias = Literal["DRIFT DETECTED", "NO DRIFT"]
INTERNET_NODE_ID = "internet"
DATABASE_NODE_ID = "database"


@dataclass(frozen=True)
class DriftFinding:
    """Result of the Internet-to-Database reachability check."""

    internet_to_database_path: bool
    status: DriftStatus
    message: str
    path: tuple[str, ...] = ()


def has_internet_to_database_path(topology: nx.DiGraph) -> bool:
    """Return whether the graph has a directed Internet-to-database path.

    Args:
        topology: Directed NetworkX graph containing the mock resource nodes.

    Returns:
        ``True`` when traffic can flow from the Internet node to the database,
        otherwise ``False``. Missing endpoint nodes are treated as no path.
    """
    if not topology.has_node(INTERNET_NODE_ID) or not topology.has_node(
        DATABASE_NODE_ID
    ):
        return False

    return nx.has_path(topology, INTERNET_NODE_ID, DATABASE_NODE_ID)


def detect_security_drift(topology: nx.DiGraph) -> DriftFinding:
    """Return a finding based on the existing Internet-to-Database path check.

    Args:
        topology: Directed NetworkX graph containing the Internet and database
            resource nodes.

    Returns:
        A :class:`DriftFinding` describing the reachability result. If no path
        exists, including when an endpoint node is missing, the finding has
        ``NO DRIFT`` status.
    """
    # NetworkX follows edge direction, so this tests whether traffic can flow
    # from the public entry point to the protected database resource.
    detected_path: tuple[str, ...] = ()
    if has_internet_to_database_path(topology):
        detected_path = tuple(
            nx.shortest_path(topology, INTERNET_NODE_ID, DATABASE_NODE_ID)
        )

    if detected_path:
        return DriftFinding(
            internet_to_database_path=True,
            status="DRIFT DETECTED",
            message=(
                "WARNING: Security Drift Detected - Internet can reach Database. "
                f"Path: {' -> '.join(detected_path)}"
            ),
            path=detected_path,
        )

    return DriftFinding(
        internet_to_database_path=False,
        status="NO DRIFT",
        message="No Internet to Database path detected",
    )
