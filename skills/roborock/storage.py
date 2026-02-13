"""Secure SQLite-backed persistence for Roborock credentials and default device."""

from __future__ import annotations

# Section: Imports
import os
import sqlite3
from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import DB_PATH


@dataclass
class RoborockCredentialRecord:
    """Structured Roborock credential payload loaded from storage."""

    user_id: str
    email: str
    encrypted_password: str
    device_id: str | None
    device_name: str | None
    device_model: str | None


class RoborockStorage:
    """SQLite persistence helper for encrypted Roborock credentials."""

    # Section: Initialization
    def __init__(self) -> None:
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create DB connection to the shared Freja SQLite database."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Create credentials table when missing."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS roborock_credentials (
                    user_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    password_encrypted TEXT NOT NULL,
                    device_id TEXT,
                    device_name TEXT,
                    device_model TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    # Section: Encryption helpers
    def _get_cipher(self) -> Fernet:
        """Initialize Fernet cipher using ROBOROCK_SECRET_KEY from environment."""
        raw_key = (os.getenv("ROBOROCK_SECRET_KEY") or "").strip()
        if not raw_key:
            raise ValueError(
                "ROBOROCK_SECRET_KEY is required. Generate with: "
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Validate key by constructing the cipher. Any invalid key raises ValueError.
        return Fernet(raw_key.encode("utf-8"))

    def encrypt_password(self, password: str) -> str:
        """Encrypt plaintext password for database storage."""
        cipher = self._get_cipher()
        return cipher.encrypt(password.encode("utf-8")).decode("utf-8")

    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt database ciphertext to plaintext password."""
        cipher = self._get_cipher()
        try:
            return cipher.decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Failed to decrypt Roborock password with current ROBOROCK_SECRET_KEY") from exc

    # Section: CRUD operations
    def get_credentials(self, user_id: str) -> Optional[RoborockCredentialRecord]:
        """Fetch credentials by user id."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, email, password_encrypted, device_id, device_name, device_model
                FROM roborock_credentials
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return RoborockCredentialRecord(
                user_id=row["user_id"],
                email=row["email"],
                encrypted_password=row["password_encrypted"],
                device_id=row["device_id"],
                device_name=row["device_name"],
                device_model=row["device_model"],
            )

    def save_credentials(
        self,
        user_id: str,
        email: str,
        password: str,
        device_id: str | None,
        device_name: str | None = None,
        device_model: str | None = None,
    ) -> None:
        """Insert or update encrypted credentials and default device metadata."""
        encrypted_password = self.encrypt_password(password)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO roborock_credentials(user_id, email, password_encrypted, device_id, device_name, device_model)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    email = excluded.email,
                    password_encrypted = excluded.password_encrypted,
                    device_id = excluded.device_id,
                    device_name = excluded.device_name,
                    device_model = excluded.device_model,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, email, encrypted_password, device_id, device_name, device_model),
            )
            conn.commit()
