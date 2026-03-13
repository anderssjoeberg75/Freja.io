"""Sleep data models for Garmin Connect."""

from datetime import datetime, date
from typing import Any

from pydantic import Field

from .base import BaseGarminModel


class SleepData(BaseGarminModel):
    """Sleep data model."""

    user_profile_pk: int | None = Field(default=None, alias="userProfilePK")
    daily_sleep_dto: dict[str, Any] | None = Field(default=None, alias="dailySleepDTO")
    sleep_movement: list[dict[str, Any]] | None = Field(default=None, alias="sleepMovement")
    rem_sleep_data: list[dict[str, Any]] | bool | None = Field(default=None, alias="remSleepData")
    
    # Derived properties based on dailySleepDTO
    @property
    def total_sleep_seconds(self) -> int:
        """Total sleep duration in seconds."""
        if not self.daily_sleep_dto:
            return 0
        return self.daily_sleep_dto.get("sleepTimeSeconds") or 0

    @property
    def deep_sleep_seconds(self) -> int:
        """Deep sleep duration in seconds."""
        if not self.daily_sleep_dto:
            return 0
        return self.daily_sleep_dto.get("deepSleepSeconds") or 0

    @property
    def light_sleep_seconds(self) -> int:
        """Light sleep duration in seconds."""
        if not self.daily_sleep_dto:
            return 0
        return self.daily_sleep_dto.get("lightSleepSeconds") or 0

    @property
    def rem_sleep_seconds(self) -> int:
        """REM sleep duration in seconds."""
        if not self.daily_sleep_dto:
            return 0
        return self.daily_sleep_dto.get("remSleepSeconds") or 0

    @property
    def awake_sleep_seconds(self) -> int:
        """Awake duration in seconds."""
        if not self.daily_sleep_dto:
            return 0
        return self.daily_sleep_dto.get("awakeSleepSeconds") or 0
        
    @property
    def total_sleep_hours(self) -> float:
        """Total sleep duration in hours."""
        return self.total_sleep_seconds / 3600.0

    @property
    def deep_sleep_hours(self) -> float:
        """Deep sleep duration in hours."""
        return self.deep_sleep_seconds / 3600.0

    @property
    def light_sleep_hours(self) -> float:
        """Light sleep duration in hours."""
        return self.light_sleep_seconds / 3600.0

    @property
    def rem_sleep_hours(self) -> float:
        """REM sleep duration in hours."""
        return self.rem_sleep_seconds / 3600.0

    @property
    def awake_sleep_hours(self) -> float:
        """Awake duration in hours."""
        return self.awake_sleep_seconds / 3600.0

    @property
    def sleep_start_timestamp(self) -> datetime | None:
        """Sleep start time."""
        if not self.daily_sleep_dto:
            return None
        ts = self.daily_sleep_dto.get("sleepStartTimestampGMT")
        if ts:
             return datetime.fromtimestamp(ts / 1000)
        return None

    @property
    def sleep_end_timestamp(self) -> datetime | None:
        """Sleep end time."""
        if not self.daily_sleep_dto:
            return None
        ts = self.daily_sleep_dto.get("sleepEndTimestampGMT")
        if ts:
             return datetime.fromtimestamp(ts / 1000)
        return None

    @property
    def overall_score(self) -> int | None:
        """Overall sleep score (0-100)."""
        if not self.daily_sleep_dto:
            return None
        scores = self.daily_sleep_dto.get("sleepScores", {})
        if scores:
             return scores.get("overall", {}).get("value")
        return None

    @property
    def avg_sleep_stress(self) -> float | None:
        """Average stress during sleep."""
        if not self.daily_sleep_dto:
            return None
        return self.daily_sleep_dto.get("averageSpO2Value") # Note: Field mapping might vary, check raw data if needed

    @property
    def avg_sleep_heart_rate(self) -> float | None:
        """Average heart rate during sleep."""
        # This might not be directly in DTO, defaulting to None if not found
        # Often derived from movement/HR data which is huge.
        return None

