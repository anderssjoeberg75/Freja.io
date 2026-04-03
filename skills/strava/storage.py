import json
import pymysql
import time
from dataclasses import dataclass
from typing import Any, Optional
from app.core.database import _get_mysql_creds

@dataclass
class TokenRecord:
    """Structured token model returned by the storage layer."""
    access_token: str
    refresh_token: str
    expires_at: int
    athlete_id: Optional[int]
    updated_at: int

class StravaStorage:
    """MySQL-backed persistence for per-user Strava tokens and API cache."""

    def __init__(self) -> None:
        self._ensure_schema()

    def _connect(self) -> pymysql.Connection:
        """Create a database connection to the remote MySQL server."""
        creds = _get_mysql_creds()
        return pymysql.connect(
            host=creds["host"],
            user=creds["user"],
            password=creds["password"],
            database=creds["db"],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def _ensure_schema(self) -> None:
        """Create required tables if they don't exist."""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strava_tokens (
                        user_id VARCHAR(255) PRIMARY KEY,
                        access_token LONGTEXT,
                        refresh_token LONGTEXT NOT NULL,
                        expires_at INTEGER NOT NULL,
                        athlete_id INTEGER,
                        updated_at INTEGER NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strava_cache (
                        user_id VARCHAR(255) NOT NULL,
                        cache_key VARCHAR(255) NOT NULL,
                        payload LONGTEXT NOT NULL,
                        expires_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        PRIMARY KEY (user_id, cache_key)
                    )
                """)
            conn.commit()

    def get_tokens(self, user_id: str) -> Optional[TokenRecord]:
        """Fetch token record from MySQL."""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT access_token, refresh_token, expires_at, athlete_id, updated_at FROM strava_tokens WHERE user_id = %s",
                    (user_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return TokenRecord(
                    access_token=row["access_token"] or "",
                    refresh_token=row["refresh_token"],
                    expires_at=int(row["expires_at"]),
                    athlete_id=row["athlete_id"],
                    updated_at=int(row["updated_at"]),
                )

    def save_tokens(self, user_id: str, access_token: str, refresh_token: str, expires_at: int, athlete_id: Optional[int]) -> None:
        """Upsert token record into MySQL."""
        updated_at = int(time.time())
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO strava_tokens (user_id, access_token, refresh_token, expires_at, athlete_id, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        access_token = VALUES(access_token),
                        refresh_token = VALUES(refresh_token),
                        expires_at = VALUES(expires_at),
                        athlete_id = VALUES(athlete_id),
                        updated_at = VALUES(updated_at)
                """, (user_id, access_token, refresh_token, expires_at, athlete_id, updated_at))
            conn.commit()

    def delete_tokens(self, user_id: str) -> None:
        """Delete tokens and cache for a user."""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM strava_tokens WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM strava_cache WHERE user_id = %s", (user_id,))
            conn.commit()

    def get_cache(self, user_id: str, cache_key: str) -> Optional[dict[str, Any]]:
        """Fetch cached payload from MySQL."""
        now = int(time.time())
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT payload, expires_at FROM strava_cache WHERE user_id = %s AND cache_key = %s",
                    (user_id, cache_key),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                if int(row["expires_at"]) <= now:
                    cursor.execute("DELETE FROM strava_cache WHERE user_id = %s AND cache_key = %s", (user_id, cache_key))
                    conn.commit()
                    return None
                return json.loads(row["payload"])

    def set_cache(self, user_id: str, cache_key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        """Upsert cache record into MySQL."""
        now = int(time.time())
        expires_at = now + ttl_seconds
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO strava_cache (user_id, cache_key, payload, expires_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        payload = VALUES(payload),
                        expires_at = VALUES(expires_at),
                        updated_at = VALUES(updated_at)
                """, (user_id, cache_key, json.dumps(payload), expires_at, now))
            conn.commit()

    def clear_cache_prefix(self, user_id: str, prefix: str) -> None:
        """Clear cache keys with a specific prefix."""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM strava_cache WHERE user_id = %s AND cache_key LIKE %s", (user_id, f"{prefix}%"))
            conn.commit()

