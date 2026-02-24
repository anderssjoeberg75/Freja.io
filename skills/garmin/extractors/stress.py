"""Stress data extractor for Garmin Connect."""

import logging
from datetime import date, datetime

from ..auth import GarminAuth
from .base import BaseExtractor
from ..models.stress import StressData

logger = logging.getLogger(__name__)


class StressExtractor(BaseExtractor[StressData]):
    """Extractor for Garmin stress data."""

    def __init__(self, auth: GarminAuth):
        """Initialize the stress extractor."""
        super().__init__(auth)

    def get_for_date(self, target_date: date | datetime | str) -> StressData | None:
        """
        Get stress data for a specific date.

        Args:
            target_date: The date to get stress data for

        Returns:
            Stress data or None if not available
        """
        date_str = self._format_date(target_date)
        try:
            # Use the stats endpoint which is more reliable
            response = self._make_request(
                f"/usersummary-service/stats/stress/daily/{date_str}/{date_str}",
            )
            if response and isinstance(response, list) and len(response) > 0:
                return StressData.from_garmin_response(response[0])
            return None
        except Exception as e:
            logger.error(f"[GARMIN] Failed to get stress data for {date_str}: {e}")
            return None

    def get_body_battery(
        self,
        target_date: date | datetime | str,
    ) -> dict | None:
        """
        Get body battery data for a specific date.

        Args:
            target_date: The date to get body battery data for

        Returns:
            Dictionary with body battery data or None
        """
        date_str = self._format_date(target_date)
        try:
            response = self._make_request(
                f"/wellness-service/wellness/bodyBattery/reports/daily",
                params={
                    "startDate": date_str,
                    "endDate": date_str,
                },
            )
            if response and isinstance(response, list) and len(response) > 0:
                return response[0]
            return None
        except Exception as e:
            logger.error(f"[GARMIN] Failed to get body battery for {date_str}: {e}")
            return None
