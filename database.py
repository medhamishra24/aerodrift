"""SQLite persistence for AeroDrift scan results."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "data" / "scan_results.db"
CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_time TEXT NOT NULL,
        status TEXT NOT NULL,
        recommendation TEXT NOT NULL
    )
"""
INSERT_RESULT_SQL = "INSERT INTO scan_results (scan_time, status, recommendation) VALUES (?, ?, ?)"


def initialize_database() -> None:
    """Create the storage directory and scan table if they do not exist.

    Raises:
        RuntimeError: If the data directory cannot be created or SQLite cannot
            create or access the scan table.
    """
    try:
        # Creating the directory here makes a fresh checkout runnable immediately.
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(CREATE_TABLE_SQL)
    except OSError as error:
        raise RuntimeError(f"Unable to create database directory: {DATABASE_PATH.parent}") from error
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to initialize SQLite database: {DATABASE_PATH}") from error


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
    scan_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
    recommendation_text = " ".join(recommendations)

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            # Parameterized SQL keeps generated recommendation text separate from the query.
            connection.execute(INSERT_RESULT_SQL, (scan_time, status, recommendation_text))
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to save scan result to SQLite database: {DATABASE_PATH}") from error
