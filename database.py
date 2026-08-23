"""SQLite persistence for AeroDrift scan results."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

DATABASE_PATH: Final[Path] = Path(__file__).parent / "data" / "scan_results.db"
CREATE_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_time TEXT NOT NULL,
        status TEXT NOT NULL,
        recommendation TEXT NOT NULL
    )
"""
INSERT_RESULT_SQL: Final[str] = (
    "INSERT INTO scan_results (scan_time, status, recommendation) VALUES (?, ?, ?)"
)


def initialize_database() -> None:
    """Create the storage directory and scan table if they do not exist.

    Raises:
        RuntimeError: If the data directory cannot be created or SQLite cannot
            create or access the scan table.
    """
    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(CREATE_TABLE_SQL)
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
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(
                INSERT_RESULT_SQL,
                (scan_time, status, recommendation_text),
            )
    except sqlite3.Error as error:
        message = f"Unable to save scan result to SQLite database: {DATABASE_PATH}"
        raise RuntimeError(message) from error
