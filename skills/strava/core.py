import httpx
import time
from app.core.config import get_credential
from app.core.database import save_db_setting


class StravaTool:
    def __init__(self):
        self.client_id = get_credential("STRAVA_CLIENT_ID")
        self.client_secret = get_credential("STRAVA_CLIENT_SECRET")
        self.refresh_token = get_credential("STRAVA_REFRESH_TOKEN")
        self.access_token = None
        self.expires_at = 0

    async def _refresh_access_token(self):
        """Fetch a new access token and persist updated refresh token."""
        latest_refresh_token = get_credential("STRAVA_REFRESH_TOKEN")
        if latest_refresh_token != self.refresh_token:
            print(">> [STRAVA] Refresh token updated in DB; invalidating cached access token.")
            self.refresh_token = latest_refresh_token
            self.access_token = None
            self.expires_at = 0

        if time.time() < self.expires_at and self.access_token:
            return True

        if not self.client_id or not self.client_secret or not self.refresh_token:
            return False

        url = "https://www.strava.com/api/v3/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            print(">> [STRAVA] Attempting to refresh token...")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=payload)
                data = response.json()

            if response.status_code == 200:
                self.access_token = data["access_token"]
                self.expires_at = data["expires_at"]
                self.refresh_token = data["refresh_token"]
                from app.core.vault import save_vault_secret
                success = save_vault_secret("STRAVA_REFRESH_TOKEN", self.refresh_token)
                if not success:
                    # Fallback to DB if Vault is disabled during migration
                    await save_db_setting("STRAVA_REFRESH_TOKEN", self.refresh_token)
                print(">> [STRAVA] Token refreshed and saved.")
                return True

            print(f">> [STRAVA] Token error: {data}")
            return False
        except Exception as exc:
            print(f">> [STRAVA] Connection error: {exc}")
            return False

    async def get_health_report(self, limit=5):
        """Fetch detailed data for recent workout sessions."""
        if not self.refresh_token:
            return {"error": "No Strava refresh token configured."}

        if not await self._refresh_access_token():
            return {"error": "Could not authenticate with Strava. Check credentials/tokens."}

        try:
            url = "https://www.strava.com/api/v3/athlete/activities"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"per_page": limit}

            print(">> [STRAVA] Fetching activities...")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                error_msg = f"Strava API responded with {response.status_code}: {response.text[:200]}"
                print(f">> [STRAVA] Error: {error_msg}")
                return {"error": error_msg}

            activities = response.json()
            if not activities:
                return {"error": "No activities found on Strava."}

            output = []
            for activity in activities:
                speed_ms = activity.get("average_speed", 0)
                speed_str = "0 km/h"

                if speed_ms > 0:
                    if activity.get("type") == "Run":
                        pace_decimal = 16.666666666667 / speed_ms
                        p_min = int(pace_decimal)
                        p_sec = int((pace_decimal - p_min) * 60)
                        speed_str = f"{p_min}:{p_sec:02d} min/km"
                    else:
                        speed_str = f"{round(speed_ms * 3.6, 1)} km/h"

                output.append(
                    {
                        "id": activity.get("id"),
                        "name": activity.get("name", "Unnamed workout"),
                        "type": activity.get("type", "Unknown"),
                        "date": activity.get("start_date_local", "")[:16].replace("T", " "),
                        "distance": f"{round(activity.get('distance', 0) / 1000, 2)} km",
                        "time": f"{round(activity.get('moving_time', 0) / 60, 0)} min",
                        "avg_hr": activity.get("average_heartrate", "N/A"),
                        "max_hr": activity.get("max_heartrate", "N/A"),
                        "elevation": f"{activity.get('total_elevation_gain', 0)} m",
                        "pace": speed_str,
                        "effort": activity.get("suffer_score", "N/A"),
                    }
                )

            print(f">> [STRAVA] Fetched {len(output)} workouts.")
            return output

        except Exception as exc:
            print(f">> [STRAVA] Fetch error: {exc}")
            return {"error": f"System error: {exc}"}
