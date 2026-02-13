"""Strava API client with normalization, caching, and retry handling."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import httpx

from app.core.config import get_credential
from skills.strava.storage import StravaStorage
from skills.strava.strava_auth import StravaAuthManager

logger = logging.getLogger(__name__)


class StravaClient:
    """HTTP client for athlete profile, stats, and activities endpoints."""

    # Section: Construction with dependency injection.
    def __init__(self, auth: StravaAuthManager, storage: StravaStorage) -> None:
        self.auth = auth
        self.storage = storage

    # Section: Public API methods.
    async def get_athlete(self, user_id: str) -> dict[str, Any]:
        cache_key = "athlete:profile"
        cached = self.storage.get_cache(user_id, cache_key)
        if cached:
            return cached

        data = await self._request(user_id, "GET", "/athlete")
        self.storage.set_cache(user_id, cache_key, data, ttl_seconds=3600)
        return data

    async def get_athlete_stats(self, user_id: str, athlete_id: int) -> dict[str, Any]:
        cache_key = f"athlete:stats:{athlete_id}"
        cached = self.storage.get_cache(user_id, cache_key)
        if cached:
            return cached

        data = await self._request(user_id, "GET", f"/athletes/{athlete_id}/stats")
        self.storage.set_cache(user_id, cache_key, data, ttl_seconds=3600)
        return data

    async def fetch_activities(
        self,
        user_id: str,
        after_ts: int,
        before_ts: int,
        page_size: int = 50,
        max_pages: int = 4,
        activity_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Fetch paginated activities with time filtering and normalized schema output."""
        cache_key = f"activities:{after_ts}:{before_ts}:{page_size}:{max_pages}:{activity_type or 'all'}"
        cached = self.storage.get_cache(user_id, cache_key)
        if cached:
            return cached.get("items", [])

        all_items: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            data = await self._request(
                user_id,
                "GET",
                "/athlete/activities",
                params={
                    "after": after_ts,
                    "before": before_ts,
                    "per_page": page_size,
                    "page": page,
                },
            )
            if not isinstance(data, list) or not data:
                break

            normalized = [self._normalize_activity(item) for item in data]
            if activity_type:
                normalized = [item for item in normalized if item.get("type", "").lower() == activity_type.lower()]
            all_items.extend(normalized)

            if len(data) < page_size:
                break

        self.storage.set_cache(user_id, cache_key, {"items": all_items}, ttl_seconds=600)
        return all_items

    # Section: Shared HTTP request handling with retry and mock support.
    async def _request(
        self,
        user_id: str,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        if self._mock_mode_enabled():
            return self._read_mock_payload(endpoint)

        access_token = await self.auth.get_access_token(user_id)
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://www.strava.com/api/v3{endpoint}"

        max_attempts = 3
        for attempt in range(max_attempts):
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.request(method, url, headers=headers, params=params)

            if res.status_code == 429 and attempt < max_attempts - 1:
                wait_seconds = 1.5 * (attempt + 1)
                logger.warning("Strava rate limit reached. Retrying in %.1f seconds", wait_seconds)
                await asyncio.sleep(wait_seconds)
                continue

            if res.status_code == 401 and attempt == 0:
                self.storage.clear_cache_prefix(user_id, "athlete:")
                self.storage.clear_cache_prefix(user_id, "activities:")
                access_token = await self.auth.get_access_token(user_id)
                headers = {"Authorization": f"Bearer {access_token}"}
                continue

            if res.status_code >= 400:
                raise RuntimeError(f"Strava API error {res.status_code}: {res.text[:220]}")

            return res.json()

        raise RuntimeError("Strava request failed after retry attempts.")

    # Section: Activity normalization helpers.
    def _normalize_activity(self, activity: dict[str, Any]) -> dict[str, Any]:
        """Normalize Strava activity to deterministic internal schema."""
        return {
            "id": activity.get("id"),
            "start_date": activity.get("start_date") or activity.get("start_date_local"),
            "type": activity.get("type", "Unknown"),
            "distance_m": float(activity.get("distance", 0.0) or 0.0),
            "moving_time_s": int(activity.get("moving_time", 0) or 0),
            "elapsed_time_s": int(activity.get("elapsed_time", 0) or 0),
            "elevation_gain_m": float(activity.get("total_elevation_gain", 0.0) or 0.0),
            "average_speed_mps": float(activity.get("average_speed", 0.0) or 0.0),
            "max_speed_mps": float(activity.get("max_speed", 0.0) or 0.0),
            "average_heartrate": activity.get("average_heartrate"),
            "max_heartrate": activity.get("max_heartrate"),
            "kudos_count": int(activity.get("kudos_count", 0) or 0),
            "achievement_count": int(activity.get("achievement_count", 0) or 0),
            "map_summary_polyline": ((activity.get("map") or {}).get("summary_polyline")),
            "name": activity.get("name", "Unnamed"),
        }

    # Section: Mock mode helpers for local/offline verification.
    def _mock_mode_enabled(self) -> bool:
        return str(get_credential("STRAVA_MOCK", "0")).strip().lower() in {"1", "true", "yes", "on"}

    def _read_mock_payload(self, endpoint: str) -> Any:
        fixture_name = str(get_credential("STRAVA_MOCK_FIXTURE", "mixed_run_ride")).strip()
        fixture_path = Path(__file__).resolve().parent / "fixtures" / f"{fixture_name}.json"
        with fixture_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if endpoint == "/athlete":
            return payload.get("athlete", {})
        if endpoint.startswith("/athletes/") and endpoint.endswith("/stats"):
            return payload.get("stats", {})
        if endpoint == "/athlete/activities":
            return payload.get("activities", [])
        return {}
