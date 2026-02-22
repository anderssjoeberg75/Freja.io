"""Authentication and OAuth helpers for Strava skill."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.core.config import get_credential
from app.core.database import save_db_setting
from skills.strava.storage import StravaStorage, TokenRecord

logger = logging.getLogger(__name__)


@dataclass
class StravaTokenResponse:
    """Parsed subset of Strava OAuth token endpoint response."""

    access_token: str
    refresh_token: str
    expires_at: int
    athlete_id: Optional[int]


class StravaAuthManager:
    """Handles Strava token bootstrap, refresh, and connect URL generation."""

    # Section: Construction and configuration access
    def __init__(self, storage: StravaStorage) -> None:
        self.storage = storage

    def _client_id(self) -> str:
        return str(get_credential("STRAVA_CLIENT_ID", "")).strip()

    def _client_secret(self) -> str:
        return str(get_credential("STRAVA_CLIENT_SECRET", "")).strip()

    def _redirect_uri(self) -> str:
        return str(get_credential("STRAVA_REDIRECT_URI", "")).strip()

    # Section: Public token resolution API
    async def get_access_token(self, user_id: str) -> str:
        """Get a valid access token, refreshing from refresh token when required."""
        record = self.storage.get_tokens(user_id)
        now = int(time.time())

        if record and record.access_token and record.expires_at > now + 30:
            return record.access_token

        if record and record.refresh_token:
            refreshed = await self._refresh_from_refresh_token(record.refresh_token)
            self.storage.save_tokens(
                user_id=user_id,
                access_token=refreshed.access_token,
                refresh_token=refreshed.refresh_token,
                expires_at=refreshed.expires_at,
                athlete_id=refreshed.athlete_id,
            )
            return refreshed.access_token

        # Section: Manual bootstrap fallback from environment credentials.
        env_refresh_token = str(get_credential("STRAVA_REFRESH_TOKEN", "")).strip()
        if env_refresh_token:
            refreshed = await self._refresh_from_refresh_token(env_refresh_token)
            self.storage.save_tokens(
                user_id=user_id,
                access_token=refreshed.access_token,
                refresh_token=refreshed.refresh_token,
                expires_at=refreshed.expires_at,
                athlete_id=refreshed.athlete_id,
            )
            return refreshed.access_token

        env_access_token = str(get_credential("STRAVA_ACCESS_TOKEN", "")).strip()
        if env_access_token:
            return env_access_token

        raise RuntimeError("Strava is not connected. Use /strava connect first.")

    def build_connect_url(self, user_id: str) -> str:
        """Build OAuth authorization URL for Telegram user to connect Strava."""
        client_id = self._client_id()
        redirect_uri = self._redirect_uri()
        if not client_id:
            raise RuntimeError("Missing STRAVA_CLIENT_ID.")
        if not redirect_uri:
            raise RuntimeError("Missing STRAVA_REDIRECT_URI.")

        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "approval_prompt": "force",
                "scope": "read,activity:read_all,profile:read_all",
                "state": user_id,
            }
        )
        return f"https://www.strava.com/oauth/authorize?{query}"

    async def exchange_code(self, user_id: str, code: str) -> StravaTokenResponse:
        """Exchange OAuth authorization code for refresh/access token pair."""
        payload = {
            "client_id": self._client_id(),
            "client_secret": self._client_secret(),
            "code": code,
            "grant_type": "authorization_code",
        }
        response = await self._call_token_endpoint(payload)
        self.storage.save_tokens(
            user_id=user_id,
            access_token=response.access_token,
            refresh_token=response.refresh_token,
            expires_at=response.expires_at,
            athlete_id=response.athlete_id,
        )
        # Also store it in global settings so strava_core.py picks it up
        await save_db_setting("STRAVA_REFRESH_TOKEN", response.refresh_token)
        return response

    async def _refresh_from_refresh_token(self, refresh_token: str) -> StravaTokenResponse:
        """Refresh token flow used by get_access_token for expired or missing access tokens."""
        payload = {
            "client_id": self._client_id(),
            "client_secret": self._client_secret(),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        return await self._call_token_endpoint(payload)

    async def _call_token_endpoint(self, payload: dict[str, str]) -> StravaTokenResponse:
        """Call Strava OAuth token endpoint and normalize result handling."""
        client_id = payload.get("client_id", "")
        client_secret = payload.get("client_secret", "")
        if not client_id or not client_secret:
            raise RuntimeError("Missing STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET.")

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post("https://www.strava.com/api/v3/oauth/token", data=payload)

        if res.status_code >= 400:
            raise RuntimeError(f"Strava OAuth failed ({res.status_code}): {res.text[:200]}")

        data = res.json()
        athlete = data.get("athlete") or {}
        token_response = StravaTokenResponse(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=int(data["expires_at"]),
            athlete_id=athlete.get("id"),
        )
        logger.debug("Strava OAuth token obtained for athlete_id=%s", token_response.athlete_id)
        return token_response

    def get_status(self, user_id: str) -> tuple[bool, Optional[TokenRecord]]:
        """Return whether a user is connected and the raw token metadata for status views."""
        record = self.storage.get_tokens(user_id)
        return (record is not None, record)

    def disconnect(self, user_id: str) -> None:
        """Disconnect user by deleting tokens and cache records."""
        self.storage.delete_tokens(user_id)
