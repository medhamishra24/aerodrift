"""Security drift checks for the cloud topology."""

from dataclasses import dataclass
from typing import Literal, TypeAlias

import networkx as nx


DriftStatus: TypeAlias = Literal["DRIFT DETECTED", "NO DRIFT"]


@dataclass(frozen=True)
class DriftFinding:
    """Result of the Internet-to-Database reachability check."""

    internet_to_database_path: bool
    status: DriftStatus
    message: str


def detect_security_drift(topology: nx.DiGraph) -> DriftFinding:
    """Return a finding based on the existing Internet-to-Database path check.

    Args:
        topology: Directed NetworkX graph containing ``internet`` and
            ``database`` resource nodes.

    Returns:
        A :class:`DriftFinding` describing the reachability result.
    """
    # NetworkX follows edge direction, so this tests whether traffic can flow
    # from the public entry point to the protected database resource.
    internet_to_database_path_exists = nx.has_path(topology, "internet", "database")

    if internet_to_database_path_exists:
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
