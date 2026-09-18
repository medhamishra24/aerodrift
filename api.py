"""Minimal JSON API for AeroDrift scan and topology data."""

from typing import Any

from fastapi import APIRouter, HTTPException

from database import get_latest_topology_diff, get_latest_topology_snapshot, get_topology_snapshot
from scan_service import run_scan_service


router = APIRouter()


def _snapshot_response(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    """Convert a stored snapshot into a JSON-safe topology response."""
    if snapshot is None:
        return None

    topology = snapshot["topology"]
    nodes = topology["nodes"]
    edges = topology["edges"]
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "timestamp": snapshot["timestamp"],
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def _database_error() -> HTTPException:
    """Return a stable API error without exposing internal database details."""
    return HTTPException(
        status_code=503,
        detail="AeroDrift history is temporarily unavailable.",
    )


@router.get("/")
def api_root() -> dict[str, str]:
    """Confirm that the AeroDrift API is running."""
    return {"name": "AeroDrift API", "status": "running"}


@router.get("/api/scan")
def scan() -> dict[str, Any]:
    """Run the existing scan service and return its structured result."""
    try:
        return run_scan_service()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="AeroDrift scan failed.",
        ) from error


@router.get("/api/topology")
def topology() -> dict[str, Any]:
    """Return the latest persisted topology snapshot."""
    try:
        snapshot = _snapshot_response(get_latest_topology_snapshot())
    except Exception as error:
        raise _database_error() from error

    if snapshot is None:
        raise HTTPException(status_code=404, detail="No topology snapshot is available.")
    return snapshot


@router.get("/api/history")
def history() -> dict[str, Any]:
    """Return the latest topology diff and its participating snapshots."""
    try:
        diff = get_latest_topology_diff()
        previous_snapshot = (
            get_topology_snapshot(snapshot_id=diff["previous_snapshot_id"])
            if diff["previous_snapshot_id"]
            else None
        )
        latest_snapshot = (
            get_topology_snapshot(snapshot_id=diff["latest_snapshot_id"])
            if diff["latest_snapshot_id"]
            else None
        )
    except Exception as error:
        raise _database_error() from error

    return {
        "status": diff["status"],
        "previous_snapshot": _snapshot_response(previous_snapshot),
        "latest_snapshot": _snapshot_response(latest_snapshot),
        "added_nodes": diff["added_nodes"],
        "removed_nodes": diff["removed_nodes"],
        "added_edges": diff["added_edges"],
        "removed_edges": diff["removed_edges"],
    }


@router.get("/api/health")
def health() -> dict[str, str]:
    """Return a lightweight service health response."""
    return {"status": "healthy", "service": "aerodrift-api"}