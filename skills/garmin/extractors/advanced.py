"""Advanced Garmin metrics extractor - Training, Health, Performance."""

import logging
from datetime import date, datetime
from typing import Any

from .base import BaseExtractor
from ..auth import GarminAuth

logger = logging.getLogger(__name__)


class AdvancedExtractor(BaseExtractor[dict]):
    """Extractor for advanced Garmin health and training metrics."""

    def __init__(self, auth: GarminAuth):
        super().__init__(auth)

    def get_for_date(self, target_date: date | datetime | str) -> dict | None:
        """Default implementation - returns training readiness for the date."""
        return self.get_training_readiness(target_date)

    # --- Training ---

    def get_training_readiness(self, target_date: date | datetime | str) -> dict | None:
        """
        Get Training Readiness score for the date.
        Factors: sleep, recovery time, HRV, ACWR, stress history.
        Returns dict with keys: score, level, sleepScore, recoveryTime, acuteLoad, etc.
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/metrics-service/metrics/trainingreadiness/{date_str}"
            )
            if resp and isinstance(resp, list) and len(resp) > 0:
                return resp[0]
            return None
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get training readiness for {date_str}: {e}")
            return None

    def get_training_status(self, target_date: date | datetime | str) -> dict | None:
        """
        Get Training Status for a date.
        Returns: trainingStatus, weeklyTrainingLoad, fitnessTrend, ACWR, acuteLoad, chronicLoad.
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/metrics-service/metrics/trainingstatus/aggregated/{date_str}"
            )
            if resp:
                most_recent = (resp.get("mostRecentTrainingStatus") or {})
                latest_data = most_recent.get("latestTrainingStatusData", {})
                # Flatten: pick first device entry
                for device_id, ts_dict in latest_data.items():
                    return ts_dict
            return None
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get training status for {date_str}: {e}")
            return None

    def get_race_predictions(self, target_date: date | datetime | str) -> dict | None:
        """
        Get Race Predictions for the date.
        Returns estimated times for 5K, 10K, Half Marathon, and Marathon.
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/metrics-service/metrics/racepredictions",
                params={"startdate": date_str, "enddate": date_str, "type": "daily"}
            )
            if resp and isinstance(resp, list) and len(resp) > 0:
                return resp[0]
            return None
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get race predictions for {date_str}: {e}")
            return None

    # --- Performance Scores ---

    def get_vo2_max(self, target_date: date | datetime | str) -> dict | None:
        """
        Get VO2 Max values for a date (running + cycling if available).
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/metrics-service/metrics/maxmet/daily/{date_str}"
            )
            if resp and isinstance(resp, list) and len(resp) > 0:
                entry = resp[0]
                return {
                    "vo2max_running": (entry.get("generic") or {}).get("vo2MaxPreciseValue"),
                    "vo2max_cycling": (entry.get("cycling") or {}).get("vo2MaxPreciseValue"),
                }
            return None
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get VO2 Max for {date_str}: {e}")
            return None

    def get_endurance_score(self, target_date: date | datetime | str) -> dict | None:
        """
        Get Endurance Score (overall composite fitness endurance score).
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/metrics-service/metrics/endurancescore",
                params={"startDate": date_str, "endDate": date_str}
            )
            if resp:
                if isinstance(resp, list) and len(resp) > 0:
                    return resp[0]
                return resp
            return None
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get endurance score for {date_str}: {e}")
            return None

    def get_hill_score(self, target_date: date | datetime | str) -> dict | None:
        """
        Get Hill Score metrics (strength, endurance, overall).
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/metrics-service/metrics/hillscore",
                params={"startDate": date_str, "endDate": date_str}
            )
            if resp:
                if isinstance(resp, list) and len(resp) > 0:
                    return resp[0]
                return resp
            return None
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get hill score for {date_str}: {e}")
            return None

    def get_fitness_age(self, target_date: date | datetime | str) -> dict | None:
        """
        Get Fitness Age data (chronologicalAge, fitnessAge, achievableFitnessAge).
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/fitnessage-service/fitnessage/",
                params={"displayDate": date_str}
            )
            return resp
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get fitness age for {date_str}: {e}")
            return None

    # --- Health ---

    def get_hrv_data(self, target_date: date | datetime | str) -> dict | None:
        """
        Get overnight HRV data (readings, weeklyAverage, status, etc.)
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/hrv-service/hrv/{date_str}"
            )
            return resp
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get HRV data for {date_str}: {e}")
            return None

    def get_hydration(self, target_date: date | datetime | str) -> dict | None:
        """
        Get daily hydration data (water intake, sweat loss, goal).
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/usersummary-service/usersummary/hydration/daily/{date_str}"
            )
            return resp
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get hydration for {date_str}: {e}")
            return None

    def get_spo2(self, target_date: date | datetime | str) -> dict | None:
        """
        Get daily SpO2 (Blood Oxygen) data.
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/wellness-service/wellness/daily/spo2/{date_str}"
            )
            return resp
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get SpO2 for {date_str}: {e}")
            return None

    def get_respiration(self, target_date: date | datetime | str) -> dict | None:
        """
        Get daily respiration (breathing rate) data.
        """
        date_str = self._format_date(target_date)
        try:
            resp = self._make_request(
                f"/wellness-service/wellness/daily/respiration/{date_str}"
            )
            return resp
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get respiration for {date_str}: {e}")
            return None

    def get_personal_records(self) -> list | None:
        """
        Get all personal records (best run time, max HR, etc.)
        from the authenticated user's Garmin Connect profile.
        """
        try:
            resp = self._make_request(
                f"/personalrecord-service/personalrecord/prs/{self.username}"
            )
            return resp
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to get personal records: {e}")
            return None
