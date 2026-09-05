"""SQLite persistence for AeroDrift scan results."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Final
from uuid import uuid4

DATABASE_PATH: Final[Path] = Path(__file__).parent / "data" / "scan_results.db"
CREATE_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_time TEXT NOT NULL,
        status TEXT NOT NULL,
        recommendation TEXT NOT NULL
    )
"""
CREATE_SNAPSHOT_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS topology_snapshots (
        snapshot_id TEXT PRIMARY KEY,
        snapshot_time TEXT NOT NULL,
        topology_data TEXT NOT NULL
    )
"""
INSERT_RESULT_SQL: Final[str] = (
    "INSERT INTO scan_results (scan_time, status, recommendation) VALUES (?, ?, ?)"
)
INSERT_SNAPSHOT_SQL: Final[str] = (
    "INSERT INTO topology_snapshots "
    "(snapshot_id, snapshot_time, topology_data) VALUES (?, ?, ?)"
)
SELECT_SNAPSHOT_BY_ID_SQL: Final[str] = (
    "SELECT snapshot_id, snapshot_time, topology_data "
    "FROM topology_snapshots WHERE snapshot_id = ?"
)
SELECT_SNAPSHOT_BY_TIME_SQL: Final[str] = (
    "SELECT snapshot_id, snapshot_time, topology_data "
    "FROM topology_snapshots WHERE snapshot_time = ? "
    "ORDER BY snapshot_id DESC LIMIT 1"
)
SELECT_RECENT_SNAPSHOTS_SQL: Final[str] = (
    "SELECT snapshot_id, snapshot_time, topology_data "
    "FROM topology_snapshots "
    "ORDER BY snapshot_time ASC, rowid ASC LIMIT ?"
)
SELECT_LATEST_SNAPSHOT_SQL: Final[str] = (
    "SELECT snapshot_id, snapshot_time, topology_data "
    "FROM topology_snapshots "
    "ORDER BY snapshot_time DESC, rowid DESC LIMIT 1"
)
COUNT_SNAPSHOTS_SQL: Final[str] = (
    "SELECT COUNT(*) FROM topology_snapshots"
)


def initialize_database() -> None:
    """Create the storage directory and scan table if they do not exist.

    Raises:
        RuntimeError: If the data directory cannot be created or SQLite cannot
            create or access the scan table.
    """
    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            with connection:
                connection.execute(CREATE_TABLE_SQL)
                connection.execute(CREATE_SNAPSHOT_TABLE_SQL)
    except OSError as error:
        message = f"Unable to create database directory: {DATABASE_PATH.parent}"
        raise RuntimeError(message) from error
    except sqlite3.Error as error:
        message = f"Unable to initialize SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error


def save_scan_result(status: str, recommendations: list[str]) -> None:
    """Persist one scan result and its recommendations in SQLite.

    Args:
        status: Human-readable scan status, such as ``DRIFT DETECTED``.
        recommendations: Recommendation messages generated for the scan.

    Raises:
        RuntimeError: If the database cannot be initialized or the result
            cannot be written.
    """
    initialize_database()
    scan_time: str = datetime.now(timezone.utc).isoformat(timespec="seconds")
    recommendation_text: str = " ".join(recommendations)

    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            with connection:
                connection.execute(
                    INSERT_RESULT_SQL,
                    (scan_time, status, recommendation_text),
                )
    except sqlite3.Error as error:
        message = f"Unable to save scan result to SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error


def save_topology_snapshot(topology: object) -> str:
    """Persist a serialized local topology snapshot and return its ID."""
    initialize_database()
    snapshot_id = uuid4().hex
    snapshot_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
    topology_data = json.dumps(
        {
            "nodes": [
                {"id": node_id, **attributes}
                for node_id, attributes in topology.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, **attributes}
                for source, target, attributes in topology.edges(data=True)
            ],
        },
        sort_keys=True,
        default=str,
    )

    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            with connection:
                connection.execute(
                    INSERT_SNAPSHOT_SQL,
                    (snapshot_id, snapshot_time, topology_data),
                )
    except sqlite3.Error as error:
        message = f"Unable to save topology snapshot to SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error
    return snapshot_id


def get_topology_snapshot(
    snapshot_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, object] | None:
    """Return one saved topology snapshot by ID or exact timestamp."""
    if snapshot_id is not None and timestamp is not None:
        raise ValueError("Provide either snapshot_id or timestamp, not both")
    if snapshot_id is None and timestamp is None:
        return None

    initialize_database()
    query = SELECT_SNAPSHOT_BY_ID_SQL if snapshot_id is not None else SELECT_SNAPSHOT_BY_TIME_SQL
    selector = snapshot_id if snapshot_id is not None else timestamp
    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            row = connection.execute(query, (selector,)).fetchone()
    except sqlite3.Error as error:
        message = f"Unable to retrieve topology snapshot from SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error

    if row is None:
        return None
    return {
        "snapshot_id": row[0],
        "timestamp": row[1],
        "topology": json.loads(row[2]),
    }


def export_topology_snapshot(snapshot_id: str) -> dict[str, object]:
    """Return a clean dictionary representation of one topology snapshot."""
    empty_snapshot = {
        "snapshot_id": None,
        "timestamp": None,
        "nodes": [],
        "edges": [],
    }
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        return empty_snapshot

    snapshot = get_topology_snapshot(snapshot_id=snapshot_id)
    if snapshot is None:
        return empty_snapshot

    topology = snapshot["topology"]
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "timestamp": snapshot["timestamp"],
        "nodes": topology["nodes"],
        "edges": topology["edges"],
    }


def validate_topology_snapshot(snapshot_id: str) -> dict[str, object]:
    """Validate the stored node and edge structure for one snapshot."""
    try:
        snapshot = export_topology_snapshot(snapshot_id)
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        return {
            "valid": False,
            "snapshot_id": snapshot_id,
            "errors": [f"Unable to read snapshot structure: {error}"],
            "message": "Topology snapshot structure is invalid.",
        }

    errors: list[str] = []
    if snapshot["snapshot_id"] is None:
        errors.append("Snapshot was not found.")

    nodes = snapshot["nodes"]
    if not isinstance(nodes, list):
        errors.append("Nodes must be a list.")
    else:
        for index, node in enumerate(nodes):
            if not isinstance(node, dict) or not node.get("id"):
                errors.append(f"Node at index {index} must include an id.")

    edges = snapshot["edges"]
    if not isinstance(edges, list):
        errors.append("Edges must be a list.")
    else:
        for index, edge in enumerate(edges):
            if (
                not isinstance(edge, dict)
                or not edge.get("source")
                or not edge.get("target")
            ):
                errors.append(
                    f"Edge at index {index} must include source and target."
                )

    return {
        "valid": not errors,
        "snapshot_id": snapshot["snapshot_id"],
        "errors": errors,
        "message": (
            "Topology snapshot structure is valid."
            if not errors
            else "Topology snapshot structure is invalid."
        ),
    }


def list_topology_snapshots(limit: int = 10) -> list[dict[str, object]]:
    """Return saved topology snapshots in chronological order."""
    if limit <= 0:
        return []

    initialize_database()
    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            rows = connection.execute(
                SELECT_RECENT_SNAPSHOTS_SQL,
                (limit,),
            ).fetchall()
    except sqlite3.Error as error:
        message = f"Unable to list topology snapshots from SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error

    return [
        {
            "snapshot_id": row[0],
            "timestamp": row[1],
            "topology": json.loads(row[2]),
        }
        for row in rows
    ]


def get_latest_topology_snapshot() -> dict[str, object] | None:
    """Return the most recently saved topology snapshot, if available."""
    initialize_database()
    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            row = connection.execute(SELECT_LATEST_SNAPSHOT_SQL).fetchone()
    except sqlite3.Error as error:
        message = f"Unable to retrieve latest topology snapshot from SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error

    if row is None:
        return None
    return {
        "snapshot_id": row[0],
        "timestamp": row[1],
        "topology": json.loads(row[2]),
    }


def count_topology_snapshots() -> int:
    """Return the number of stored topology snapshots."""
    initialize_database()
    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            row = connection.execute(COUNT_SNAPSHOTS_SQL).fetchone()
    except sqlite3.Error as error:
        message = f"Unable to count topology snapshots in SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error
    return int(row[0]) if row is not None else 0


def topology_history_available() -> bool:
    """Return whether at least two snapshots are available for comparison."""
    return count_topology_snapshots() >= 2


def compare_topology_snapshots(
    first_snapshot_id: str,
    second_snapshot_id: str,
) -> dict[str, object] | None:
    """Return added and removed nodes and edges between two snapshots."""
    first_snapshot = get_topology_snapshot(snapshot_id=first_snapshot_id)
    second_snapshot = get_topology_snapshot(snapshot_id=second_snapshot_id)
    if first_snapshot is None or second_snapshot is None:
        return None

    first_topology = first_snapshot["topology"]
    second_topology = second_snapshot["topology"]
    first_nodes = {node["id"]: node for node in first_topology["nodes"]}
    second_nodes = {node["id"]: node for node in second_topology["nodes"]}
    first_edges = {
        (edge["source"], edge["target"]): edge
        for edge in first_topology["edges"]
    }
    second_edges = {
        (edge["source"], edge["target"]): edge
        for edge in second_topology["edges"]
    }

    return {
        "first_snapshot_id": first_snapshot_id,
        "second_snapshot_id": second_snapshot_id,
        "added_nodes": [
            second_nodes[node_id]
            for node_id in sorted(second_nodes.keys() - first_nodes.keys())
        ],
        "removed_nodes": [
            first_nodes[node_id]
            for node_id in sorted(first_nodes.keys() - second_nodes.keys())
        ],
        "added_edges": [
            second_edges[edge]
            for edge in sorted(second_edges.keys() - first_edges.keys())
        ],
        "removed_edges": [
            first_edges[edge]
            for edge in sorted(first_edges.keys() - second_edges.keys())
        ],
    }


def get_latest_topology_diff() -> dict[str, object]:
    """Return the diff between the latest and previous snapshots."""
    snapshots = list_topology_snapshots(limit=2)
    if len(snapshots) < 2:
        return {
            "status": "NO HISTORY",
            "previous_snapshot_id": None,
            "latest_snapshot_id": snapshots[0]["snapshot_id"]
            if snapshots
            else None,
            "added_nodes": [],
            "removed_nodes": [],
            "added_edges": [],
            "removed_edges": [],
        }

    previous_snapshot_id = snapshots[0]["snapshot_id"]
    latest_snapshot_id = snapshots[1]["snapshot_id"]
    diff = compare_topology_snapshots(previous_snapshot_id, latest_snapshot_id)
    if diff is None:
        return {
            "status": "NO HISTORY",
            "previous_snapshot_id": previous_snapshot_id,
            "latest_snapshot_id": latest_snapshot_id,
            "added_nodes": [],
            "removed_nodes": [],
            "added_edges": [],
            "removed_edges": [],
        }

    return {
        "status": "CHANGES DETECTED"
        if any(
            diff[key]
            for key in ("added_nodes", "removed_nodes", "added_edges", "removed_edges")
        )
        else "NO CHANGE",
        "previous_snapshot_id": previous_snapshot_id,
        "latest_snapshot_id": latest_snapshot_id,
        "added_nodes": diff["added_nodes"],
        "removed_nodes": diff["removed_nodes"],
        "added_edges": diff["added_edges"],
        "removed_edges": diff["removed_edges"],
    }


def has_topology_changes(
    first_snapshot_id: str,
    second_snapshot_id: str,
    include_diff: bool = False,
) -> bool | tuple[bool, dict[str, object] | None]:
    """Return whether two snapshots differ, optionally with their diff."""
    if (
        not isinstance(first_snapshot_id, str)
        or not first_snapshot_id.strip()
        or not isinstance(second_snapshot_id, str)
        or not second_snapshot_id.strip()
    ):
        diff = None
    else:
        diff = compare_topology_snapshots(first_snapshot_id, second_snapshot_id)

    has_changes = diff is not None and any(
        diff[key] for key in ("added_nodes", "removed_nodes", "added_edges", "removed_edges")
    )
    return (has_changes, diff) if include_diff else has_changes


def summarize_topology_diff(
    first_snapshot_id: str,
    second_snapshot_id: str,
) -> str:
    """Return a concise human-readable summary of a snapshot diff."""
    diff = compare_topology_snapshots(first_snapshot_id, second_snapshot_id)
    if diff is None:
        return "Topology diff unavailable: one or both snapshots were not found."

    added_nodes = diff["added_nodes"]
    removed_nodes = diff["removed_nodes"]
    added_edges = diff["added_edges"]
    removed_edges = diff["removed_edges"]
    if not any((added_nodes, removed_nodes, added_edges, removed_edges)):
        return (
            f"No topology changes between snapshots {first_snapshot_id} "
            f"and {second_snapshot_id}."
        )

    def format_nodes(nodes: list[dict[str, object]]) -> str:
        return ", ".join(str(node["id"]) for node in nodes) or "none"

    def format_edges(edges: list[dict[str, object]]) -> str:
        return ", ".join(
            f"{edge['source']} -> {edge['target']}" for edge in edges
        ) or "none"

    return (
        f"Topology changes from {first_snapshot_id} to {second_snapshot_id}: "
        f"added nodes ({len(added_nodes)}): {format_nodes(added_nodes)}; "
        f"removed nodes ({len(removed_nodes)}): {format_nodes(removed_nodes)}; "
        f"added edges ({len(added_edges)}): {format_edges(added_edges)}; "
        f"removed edges ({len(removed_edges)}): {format_edges(removed_edges)}."
    )
