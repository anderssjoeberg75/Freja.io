"""Storage primitives for Strava skill tokens and cache."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Optional

from app.core.config import DB_PATH


@dataclass
class TokenRecord:
    """Structured token model returned by the storage layer."""

    access_token: str
    refresh_token: str
    expires_at: int
    athlete_id: Optional[int]
    updated_at: int


class StravaStorage:
    """SQLite-backed persistence for per-user Strava tokens and API cache."""

    # Section: Initialization and schema setup
    def __init__(self) -> None:
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection to the shared Freja DB path."""
        conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Create required tables when they do not already exist."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strava_tokens (
                    user_id TEXT PRIMARY KEY,
                    access_token TEXT,
                    refresh_token TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    athlete_id INTEGER,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strava_cache (
                    user_id TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY (user_id, cache_key)
                )
                """
            )
            conn.commit()

    # Section: Token persistence
    def get_tokens(self, user_id: str) -> Optional[TokenRecord]:
        """Fetch token record for a specific Telegram user/chat identifier."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT access_token, refresh_token, expires_at, athlete_id, updated_at FROM strava_tokens WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return TokenRecord(
                access_token=row["access_token"] or "",
                refresh_token=row["refresh_token"],
                expires_at=int(row["expires_at"]),
                athlete_id=row["athlete_id"],
                updated_at=int(row["updated_at"]),
            )

    def save_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        expires_at: int,
        athlete_id: Optional[int],
    ) -> None:
        """Insert or update token record for a specific user."""
        updated_at = int(time.time())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strava_tokens(user_id, access_token, refresh_token, expires_at, athlete_id, updated_at)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_at = excluded.expires_at,
                    athlete_id = excluded.athlete_id,
                    updated_at = excluded.updated_at
                """,
                (user_id, access_token, refresh_token, expires_at, athlete_id, updated_at),
            )
            conn.commit()

    def delete_tokens(self, user_id: str) -> None:
        """Delete token and cache data to fully disconnect Strava for one user."""
        with self._connect() as conn:
            conn.execute("DELETE FROM strava_tokens WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM strava_cache WHERE user_id = ?", (user_id,))
            conn.commit()

    # Section: Generic cache helpers
    def get_cache(self, user_id: str, cache_key: str) -> Optional[dict[str, Any]]:
        """Return cached payload when present and not expired."""
        now = int(time.time())
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, expires_at FROM strava_cache WHERE user_id = ? AND cache_key = ?",
                (user_id, cache_key),
            ).fetchone()
            if not row:
                return None
            if int(row["expires_at"]) <= now:
                conn.execute(
                    "DELETE FROM strava_cache WHERE user_id = ? AND cache_key = ?",
                    (user_id, cache_key),
                )
                conn.commit()
                return None
            return json.loads(row["payload"])

    def set_cache(self, user_id: str, cache_key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        """Store serialized cache payload with expiration timestamp."""
        now = int(time.time())
        expires_at = now + ttl_seconds
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strava_cache(user_id, cache_key, payload, expires_at, updated_at)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(user_id, cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    expires_at = excluded.expires_at,
                    updated_at = excluded.updated_at
                """,
                (user_id, cache_key, json.dumps(payload), expires_at, now),
            )
            conn.commit()

    def clear_cache_prefix(self, user_id: str, prefix: str) -> None:
        """Clear all cache keys that start with a prefix for invalidation flows."""
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM strava_cache WHERE user_id = ? AND cache_key LIKE ?",
                (user_id, f"{prefix}%"),
            )
            conn.commit()
