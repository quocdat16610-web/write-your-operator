"""SQLite storage. Each schema change is a numbered migration tracked by PRAGMA user_version."""
from __future__ import annotations

import sqlite3
from pathlib import Path

# Migration N upgrades the schema from version N to N+1. Later steps append to this list.
MIGRATIONS: list[str] = [
    """
    CREATE TABLE settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE lesson_progress (
        lesson_id         TEXT PRIMARY KEY,
        status            TEXT NOT NULL DEFAULT 'not_started'
                          CHECK (status IN ('not_started', 'in_progress', 'done')),
        manually_unlocked INTEGER NOT NULL DEFAULT 0,
        started_at        TEXT,
        completed_at      TEXT,
        updated_at        TEXT NOT NULL
    );
    """,
]


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        for index in range(version, len(MIGRATIONS)):
            with self.conn:
                self.conn.executescript(MIGRATIONS[index])
                self.conn.execute(f"PRAGMA user_version = {index + 1}")

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def close(self) -> None:
        self.conn.close()
