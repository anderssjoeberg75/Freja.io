import datetime
import time

import requests

from app.core.config import get_credential
from app.core.database import save_db_setting


class WithingsTool:
    def __init__(self):
        self.client_id = get_credential("WITHINGS_CLIENT_ID")
        self.client_secret = get_credential("WITHINGS_CLIENT_SECRET")
        self.refresh_token = get_credential("WITHINGS_REFRESH_TOKEN")
        self.access_token = None
        self.expires_at = 0

    def exchange_code(self, code, redirect_uri):
        url = "https://wbsapi.withings.net/v2/oauth2"
        payload = {
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        try:
            response = requests.post(url, data=payload)
            data = response.json()

            if data.get("status") == 0:
                body = data["body"]
                self.access_token = body["access_token"]
                self.expires_at = time.time() + body["expires_in"] - 60
                self.refresh_token = body["refresh_token"]
                save_db_setting("WITHINGS_REFRESH_TOKEN", self.refresh_token)
                return True, "Withings connected successfully."

            return False, f"Withings token exchange error: {data}"
        except Exception as exc:
            return False, f"Withings connection error: {exc}"

    def _refresh_access_token(self):
        latest_refresh_token = get_credential("WITHINGS_REFRESH_TOKEN")
        if latest_refresh_token != self.refresh_token:
            self.refresh_token = latest_refresh_token
            self.access_token = None
            self.expires_at = 0

        if time.time() < self.expires_at and self.access_token:
            return

        url = "https://wbsapi.withings.net/v2/oauth2"
        payload = {
            "action": "requesttoken",
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(url, data=payload)
            data = response.json()

            if data.get("status") == 0:
                body = data["body"]
                self.access_token = body["access_token"]
                self.expires_at = time.time() + body["expires_in"] - 60
                self.refresh_token = body["refresh_token"]
                save_db_setting("WITHINGS_REFRESH_TOKEN", self.refresh_token)
            else:
                print(f">> [WITHINGS] Token refresh error: {data}")
        except Exception as exc:
            print(f">> [WITHINGS] Connection error: {exc}")

    def get_health_report(self):
        if not self.refresh_token:
            return {"error": "No Withings refresh token configured."}

        self._refresh_access_token()

        if not self.access_token:
            return {"error": "No access to Withings."}

        headers = {"Authorization": f"Bearer {self.access_token}"}
        report = {}

        try:
            today = datetime.date.today().strftime("%Y-%m-%d")

            act_url = "https://wbsapi.withings.net/v2/measure"
            act_params = {
                "action": "getactivity",
                "startdateymd": today,
                "enddateymd": today,
                "data_fields": "steps,distance,elevation,soft,moderate,intense,active,calories,totalcalories,hr_average,hr_min,hr_max",
            }
            act_response = requests.post(act_url, headers=headers, data=act_params)
            act_data = act_response.json()

            if (
                act_data.get("status") == 0
                and "body" in act_data
                and "activities" in act_data["body"]
                and act_data["body"]["activities"]
            ):
                latest = act_data["body"]["activities"][-1]
                report["steps_withings"] = latest.get("steps", 0)
                report["total_calories"] = latest.get("totalcalories", 0)
                report["active_minutes"] = round(latest.get("active", 0) / 60, 0)
                if "hr_average" in latest:
                    report["avg_hr"] = latest["hr_average"]

            meas_url = "https://wbsapi.withings.net/measure"
            meas_params = {"action": "getmeas", "category": 1, "limit": 1}
            meas_response = requests.post(meas_url, headers=headers, data=meas_params)
            meas_data = meas_response.json()

            if (
                meas_data.get("status") == 0
                and "body" in meas_data
                and "measuregrps" in meas_data["body"]
                and meas_data["body"]["measuregrps"]
            ):
                group = meas_data["body"]["measuregrps"][0]
                report["measurement_time"] = datetime.datetime.fromtimestamp(group["date"]).strftime(
                    "%Y-%m-%d %H:%M"
                )

                for measure in group["measures"]:
                    value = measure["value"] * (10 ** measure["unit"])
                    metric_type = measure["type"]

                    if metric_type == 1:
                        report["weight_kg"] = round(value, 1)
                    elif metric_type == 6:
                        report["fat_percent"] = round(value, 1)
                    elif metric_type == 76:
                        report["muscle_mass_kg"] = round(value, 1)
                    elif metric_type == 77:
                        report["water_kg"] = round(value, 1)
                    elif metric_type == 88:
                        report["bone_mass_kg"] = round(value, 1)
                    elif metric_type == 9:
                        report["blood_pressure_diastolic"] = int(value)
                    elif metric_type == 10:
                        report["blood_pressure_systolic"] = int(value)
                    elif metric_type == 11:
                        report["heart_rate_at_measurement"] = int(value)

            return report
        except Exception as exc:
            return {"error": f"Withings fetch error: {exc}"}
