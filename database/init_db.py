"""
Database initialization and management for AI Meeting Intelligence SaaS.
Creates and manages the SQLite database schema.
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "meetings.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create the database and all required tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_name    TEXT NOT NULL,
            upload_date     TEXT NOT NULL,
            transcript      TEXT,
            summary         TEXT,
            action_items    TEXT,
            decisions       TEXT,
            deadlines       TEXT,
            word_count      INTEGER DEFAULT 0,
            speaker_count   INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)


def save_meeting(
    meeting_name: str,
    upload_date: str,
    transcript: str,
    summary: str,
    action_items: str,
    decisions: str,
    deadlines: str,
    word_count: int = 0,
    speaker_count: int = 0,
) -> int:
    """Insert a new meeting record and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO meetings
            (meeting_name, upload_date, transcript, summary,
             action_items, decisions, deadlines, word_count, speaker_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            meeting_name,
            upload_date,
            transcript,
            summary,
            action_items,
            decisions,
            deadlines,
            word_count,
            speaker_count,
        ),
    )

    meeting_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info("Saved meeting '%s' with id=%d", meeting_name, meeting_id)
    return meeting_id


def fetch_all_meetings() -> list[dict]:
    """Return all meetings ordered by upload date descending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meetings ORDER BY upload_date DESC"
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def fetch_meeting_by_id(meeting_id: int) -> dict | None:
    """Return a single meeting by ID, or None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_meeting(meeting_id: int) -> None:
    """Delete a meeting record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()
    logger.info("Deleted meeting id=%d", meeting_id)
