"""Daily summary data extractor for Garmin Connect."""

import logging
from datetime import date, datetime, timedelta

from ..auth import GarminAuth
from .base import BaseExtractor
from ..models.daily import DailySummary

logger = logging.getLogger(__name__)


class DailyExtractor(BaseExtractor[DailySummary]):
    """Extractor for Garmin daily summary data."""

    def __init__(self, auth: GarminAuth):
        """Initialize the daily summary extractor."""
        super().__init__(auth)

    def get_for_date(self, target_date: date | datetime | str) -> DailySummary | None:
        """
        Get daily summary for a specific date.

        Args:
            target_date: The date to get the summary for

        Returns:
            Daily summary or None if not available
        """
        date_str = self._format_date(target_date)
        try:
            response = self._make_request(
                f"/usersummary-service/usersummary/daily/?calendarDate={date_str}",
            )
            if response:
                return DailySummary.from_garmin_response(response)
            return None
        except Exception as e:
            logger.error(f"[GARMIN] Failed to get daily summary for {date_str}: {e}")
            return None
