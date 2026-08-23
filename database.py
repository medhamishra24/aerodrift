"""SQLite persistence for AeroDrift scan results."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "data" / "scan_results.db"


def initialize_database() -> None:
    """Create the data directory and scan table when needed."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_time TEXT NOT NULL,
                status TEXT NOT NULL,
                recommendation TEXT NOT NULL
            )
            """
        )


def save_scan_result(status: str, recommendations: list[str]) -> None:
    """Persist one scan result and its recommendations."""
    initialize_database()
    scan_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
    recommendation_text = " ".join(recommendations)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "INSERT INTO scan_results (scan_time, status, recommendation) VALUES (?, ?, ?)",
            (scan_time, status, recommendation_text),
        )
