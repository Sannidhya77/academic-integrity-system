import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent / "database.db"


def get_connection():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_submission(filename: str, content: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO submissions (filename, content) VALUES (?, ?)",
            (filename, content),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def fetch_all_submissions():
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT id, filename, content, timestamp FROM submissions ORDER BY id ASC"
        )
        return cur.fetchall()
    finally:
        conn.close()


def count_submissions():
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM submissions").fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def count_submissions_recent_days(days: int = 7) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n FROM submissions
            WHERE timestamp >= datetime('now', ?)
            """,
            (f"-{int(days)} days",),
        ).fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def fetch_recent_submissions(limit: int = 20):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT id, filename, timestamp
            FROM submissions
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        return cur.fetchall()
    finally:
        conn.close()
