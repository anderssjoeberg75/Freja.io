"""Core Fitbit client used by the Fitbit skill."""

from __future__ import annotations

import base64
import datetime as dt
import time
from typing import Any

import httpx

from app.core.config import get_credential


class FitbitTool:
    """Fetch daily Fitbit health and activity data using OAuth refresh tokens."""

    def __init__(self) -> None:
        self.client_id = get_credential("FITBIT_CLIENT_ID")
        self.client_secret = get_credential("FITBIT_CLIENT_SECRET")
        self.refresh_token = get_credential("FITBIT_REFRESH_TOKEN")
        self.access_token: str | None = None
        self.expires_at = 0

    async def _refresh_access_token(self) -> bool:
        """Refresh the Fitbit OAuth access token when needed."""
        latest_refresh_token = get_credential("FITBIT_REFRESH_TOKEN")
        if latest_refresh_token != self.refresh_token:
            self.refresh_token = latest_refresh_token
            self.access_token = None
            self.expires_at = 0

        if self.access_token and time.time() < self.expires_at:
            return True

        if not self.client_id or not self.client_secret or not self.refresh_token:
            return False

        basic_auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.fitbit.com/oauth2/token", data=payload, headers=headers)

        if response.status_code != 200:
            return False

        data = response.json()
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        expires_in = int(data.get("expires_in", 3600))
        self.expires_at = time.time() + expires_in - 60

        try:
            from app.core.vault import save_vault_secret

            save_vault_secret("FITBIT_REFRESH_TOKEN", self.refresh_token)
        except Exception:
            # Non-blocking fallback: runtime still works with in-memory token.
            pass

        return bool(self.access_token)

    async def exchange_code(self, code: str, redirect_uri: str) -> tuple[bool, str]:
        """Exchange OAuth 2.0 authorization code for access and refresh tokens."""
        if not self.client_id or not self.client_secret:
            return False, "Fitbit client ID or secret not configured."

        basic_auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "clientId": self.client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.fitbit.com/oauth2/token", data=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            expires_in = int(data.get("expires_in", 3600))
            self.expires_at = time.time() + expires_in - 60

            if self.refresh_token:
                try:
                    from app.core.vault import save_vault_secret
                    save_vault_secret("FITBIT_REFRESH_TOKEN", self.refresh_token)
                    return True, "Fitbit connected successfully."
                except Exception as exc:
                    return False, f"Connected, but failed to save token to Vault: {exc}"
            return False, "Token exchange succeeded but no refresh token received."
        else:
            return False, f"Token exchange failed: {response.text}"

    async def _fetch_json(self, client: httpx.AsyncClient, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call a Fitbit API endpoint and return parsed JSON."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await client.get(f"https://api.fitbit.com{path}", headers=headers, params=params)
        if response.status_code != 200:
            raise RuntimeError(f"Fitbit API error {response.status_code}: {response.text[:200]}")
        return response.json()

    async def get_health_report(self, activities_limit: int = 5) -> dict[str, Any]:
        """Return Fitbit daily summary, sleep details, and recent activities."""
        if not self.refresh_token:
            return {"error": "No Fitbit refresh token configured."}

        if not await self._refresh_access_token():
            return {"error": "Could not authenticate with Fitbit. Check credentials and refresh token."}

        today = dt.date.today().isoformat()
        month_ago = (dt.date.today() - dt.timedelta(days=30)).isoformat()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                daily_data = await self._fetch_json(client, f"/1/user/-/activities/date/{today}.json")
                sleep_data = await self._fetch_json(client, f"/1.2/user/-/sleep/date/{today}.json")
                activities_data = await self._fetch_json(
                    client,
                    "/1/user/-/activities/list.json",
                    params={
                        "afterDate": month_ago,
                        "sort": "desc",
                        "offset": 0,
                        "limit": max(1, min(activities_limit, 20)),
                    },
                )

            summary = daily_data.get("summary", {})
            sleep_summary = sleep_data.get("summary", {})
            recent = []
            for item in activities_data.get("activities", []):
                recent.append(
                    {
                        "name": item.get("activityName"),
                        "start_time": item.get("startTime"),
                        "duration_minutes": round((item.get("duration", 0) or 0) / 60000, 1),
                        "calories": item.get("calories"),
                        "steps": item.get("steps"),
                        "distance_km": round((item.get("distance", 0) or 0) / 1000, 2),
                    }
                )

            return {
                "date": today,
                "steps": summary.get("steps"),
                "distance_km": round((summary.get("distances", [{}])[0].get("distance", 0) or 0), 2),
                "calories_out": summary.get("caloriesOut"),
                "active_zone_minutes": summary.get("activeZoneMinutes", {}),
                "resting_heart_rate": summary.get("restingHeartRate"),
                "sleep_total_minutes": sleep_summary.get("totalMinutesAsleep"),
                "sleep_efficiency": sleep_summary.get("efficiency"),
                "sleep_stages": sleep_summary.get("stages"),
                "recent_activities": recent,
            }
        except Exception as exc:
            return {"error": f"Fitbit fetch error: {exc}"}
