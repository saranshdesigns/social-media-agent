"""
SQLite database setup and helper functions.
Tracks posted images, scheduled queue, platform logs, and system settings.
"""
import sqlite3
import os
from datetime import datetime
from config import get_settings

settings = get_settings()


def get_db_path() -> str:
    path = os.path.abspath(settings.database_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # returns dict-like rows
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- posted_images: permanent record of every uploaded image ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posted_images (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_file_id   TEXT NOT NULL UNIQUE,
            file_name       TEXT NOT NULL,
            folder_path     TEXT,
            posted_at       TEXT NOT NULL,
            instagram       INTEGER DEFAULT 0,
            facebook        INTEGER DEFAULT 0,
            caption_used    TEXT,
            cloudinary_url  TEXT
        )
    """)

    # --- post_queue: images staged for today's posting run ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_queue (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_file_id   TEXT NOT NULL,
            file_name       TEXT NOT NULL,
            folder_path     TEXT,
            scheduled_at    TEXT,
            status          TEXT DEFAULT 'pending',
            created_at      TEXT NOT NULL
        )
    """)

    # --- platform_logs: per-platform success/error per post ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_file_id   TEXT NOT NULL,
            platform        TEXT NOT NULL,
            status          TEXT NOT NULL,
            response        TEXT,
            attempt         INTEGER DEFAULT 1,
            logged_at       TEXT NOT NULL
        )
    """)

    # --- settings: key-value store for runtime toggles ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL
        )
    """)

    # Default settings
    defaults = [
        ("automation_paused", "false"),
        ("last_run_at", ""),
        ("next_run_at", ""),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)",
        defaults
    )

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


# ── Helper functions ─────────────────────────────────────────────────────────

def is_already_posted(drive_file_id: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM posted_images WHERE drive_file_id = ?",
        (drive_file_id,)
    ).fetchone()
    conn.close()
    return row is not None


def mark_as_posted(
    drive_file_id: str,
    file_name: str,
    folder_path: str,
    caption: str,
    cloudinary_url: str,
    platforms: dict  # e.g. {"instagram": True, "facebook": True, ...}
):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO posted_images
        (drive_file_id, file_name, folder_path, posted_at, instagram,
         facebook, caption_used, cloudinary_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        drive_file_id,
        file_name,
        folder_path,
        datetime.utcnow().isoformat(),
        int(platforms.get("instagram", False)),
        int(platforms.get("facebook", False)),
        caption,
        cloudinary_url
    ))
    conn.commit()
    conn.close()


def log_platform_result(
    drive_file_id: str,
    platform: str,
    status: str,
    response: str = "",
    attempt: int = 1
):
    conn = get_connection()
    conn.execute("""
        INSERT INTO platform_logs
        (drive_file_id, platform, status, response, attempt, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (drive_file_id, platform, status, response, attempt, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_setting(key: str) -> str:
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM system_settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else ""


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


def get_posted_history(limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM posted_images ORDER BY posted_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_logs(limit: int = 100) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM platform_logs ORDER BY logged_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
