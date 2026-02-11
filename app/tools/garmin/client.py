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
