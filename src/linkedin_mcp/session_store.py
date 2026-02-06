"""SQLite-backed token and session storage for multi-user LinkedIn OAuth.

Provides a minimal per-user token store suitable for a POC deployment.
Schema: user_id, access_token, refresh_token, expires_at, created_at.

For production, replace with a proper secret manager / encrypted store.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path


class SessionStore:
    """SQLite store that maps user_id -> LinkedIn OAuth tokens."""

    DDL = """
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id       TEXT PRIMARY KEY,
        access_token  TEXT NOT NULL,
        refresh_token TEXT,
        expires_at    REAL,
        created_at    REAL NOT NULL
    );
    """

    def __init__(self, db_path: str | Path = "linkedin_sessions.db"):
        self.db_path = str(db_path)
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(self.DDL)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_token(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
    ) -> None:
        """Insert or replace tokens for *user_id*."""
        now = time.time()
        expires_at = (now + expires_in) if expires_in else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_tokens
                    (user_id, access_token, refresh_token, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, access_token, refresh_token, expires_at, now),
            )

    def get_token(self, user_id: str) -> dict | None:
        """Return token dict for *user_id* or ``None``."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT access_token, refresh_token, expires_at, created_at "
                "FROM user_tokens WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "user_id": user_id,
            "access_token": row[0],
            "refresh_token": row[1],
            "expires_at": row[2],
            "created_at": row[3],
        }

    def get_active_token(self) -> dict | None:
        """Return the most-recently stored token (POC: single active user).

        For multi-user production, the caller should use ``get_token(user_id)``
        instead with a proper session→user mapping.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, access_token, refresh_token, expires_at, created_at "
                "FROM user_tokens ORDER BY created_at DESC LIMIT 1",
            ).fetchone()
        if row is None:
            return None
        return {
            "user_id": row[0],
            "access_token": row[1],
            "refresh_token": row[2],
            "expires_at": row[3],
            "created_at": row[4],
        }

    def delete_token(self, user_id: str) -> None:
        """Remove tokens for *user_id*."""
        with self._connect() as conn:
            conn.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))

    def is_token_expired(self, user_id: str) -> bool:
        """Return True if the token exists and is past its expiry."""
        tok = self.get_token(user_id)
        if tok is None:
            return True
        if tok["expires_at"] is None:
            return False
        return time.time() > tok["expires_at"]
