"""Main Garmin Client."""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .auth import GarminAuth
from .extractors import (
    DailyExtractor,
    SleepExtractor,
    StressExtractor,
    AdvancedExtractor,
)

logger = logging.getLogger(__name__)


class GarminClient:
    """
    Main client for Garmin data extraction.
    """

    def __init__(
        self,
        auth: GarminAuth | None = None,
        token_dir: Path | str | None = None,
    ):
        """
        Initialize the Garmin client.

        Args:
            auth: Optional pre-configured GarminAuth instance
            token_dir: Directory to store authentication tokens
        """
        self.auth = auth or GarminAuth(token_dir=token_dir)

        # Initialize extractors
        self._sleep = SleepExtractor(self.auth)
        self._stress = StressExtractor(self.auth)
        self._daily = DailyExtractor(self.auth)
        self._advanced = AdvancedExtractor(self.auth)

    @classmethod
    def from_credentials(
        cls,
        email: str | None = None,
        password: str | None = None,
    ) -> "GarminClient":
        """
        Create a client and login with credentials.
        """
        auth = GarminAuth()
        auth.login(email, password)
        return cls(auth=auth)

    def login(self) -> bool:
        """Login to Garmin Connect using configured credentials."""
        return self.auth.login()

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self.auth.is_authenticated

    # --- Delegate methods to extractors ---

    def get_daily_summary(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get daily summary for a date (defaults to today)."""
        target_date = target_date or date.today()
        return self._daily.get_for_date(target_date)

    def get_sleep(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get sleep data for a date (defaults to today)."""
        target_date = target_date or date.today()
        return self._sleep.get_for_date(target_date)

    def get_stress(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get stress data for a date (defaults to today)."""
        target_date = target_date or date.today()
        return self._stress.get_for_date(target_date)

    def get_body_battery(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get body battery data for a date (defaults to today)."""
        target_date = target_date or date.today()
        return self._stress.get_body_battery(target_date)

    # --- Advanced / New Metrics ---

    def get_training_readiness(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get Training Readiness score for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_training_readiness(target_date)

    def get_training_status(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get Training Status (load, fitness trend, ACWR) for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_training_status(target_date)

    def get_race_predictions(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get Race Predictions (5K, 10K, Half Marathon, Marathon) for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_race_predictions(target_date)

    def get_vo2_max(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get VO2 Max values (running + cycling) for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_vo2_max(target_date)

    def get_endurance_score(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get Endurance Score for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_endurance_score(target_date)

    def get_hill_score(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get Hill Score (strength + endurance) for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_hill_score(target_date)

    def get_fitness_age(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get Fitness Age data for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_fitness_age(target_date)

    def get_hrv_data(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get overnight HRV data for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_hrv_data(target_date)

    def get_hydration(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get daily hydration (water intake + sweat loss) for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_hydration(target_date)

    def get_spo2(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get daily SpO2 (blood oxygen) data for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_spo2(target_date)

    def get_respiration(
        self,
        target_date: date | datetime | str | None = None,
    ):
        """Get daily respiration (breathing rate) data for a date."""
        target_date = target_date or date.today()
        return self._advanced.get_respiration(target_date)

    def get_personal_records(self):
        """Get all personal records from Garmin Connect profile."""
        return self._advanced.get_personal_records()

