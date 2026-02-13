"""Stress data models for Garmin stress monitoring."""

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import BaseGarminModel


class StressSample(BaseGarminModel):
    """A single stress measurement sample."""

    timestamp: datetime | None = None
    stress_level: int = Field(default=-1)  # -1 indicates no measurement
    
    @classmethod
    def from_garmin_response(cls, data: dict[str, Any]) -> "StressSample":
        # Handle list format [timestamp_ms, stress_level]
        if isinstance(data, list) and len(data) >= 2:
            ts = data[0]
            level = data[1]
            return cls(
                timestamp=datetime.fromtimestamp(ts/1000) if ts else None,
                stress_level=level if level is not None else -1
            )
            
        # Handle dict format
        ts = data.get("timestamp")
        return cls(
            timestamp=datetime.fromtimestamp(ts/1000) if ts else None,
            stress_level=data.get("stressLevel", -1),
        )

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid stress measurement."""
        return self.stress_level >= 0


class StressData(BaseGarminModel):
    """Stress data for a specific day."""

    # Date info
    calendar_date: str | None = Field(alias="calendarDate", default=None)
    start_timestamp: datetime | None = Field(alias="startTimestampGMT", default=None)
    end_timestamp: datetime | None = Field(alias="endTimestampGMT", default=None)

    # Summary statistics
    overall_stress_level: int | None = Field(alias="overallStressLevel", default=None)
    avg_stress_level: int | None = Field(alias="avgStressLevel", default=None)
    max_stress_level: int | None = Field(alias="maxStressLevel", default=None)

    # Time in different stress states (in seconds)
    rest_stress_duration: int = Field(alias="restStressDuration", default=0)
    low_stress_duration: int = Field(alias="lowStressDuration", default=0)
    medium_stress_duration: int = Field(alias="mediumStressDuration", default=0)
    high_stress_duration: int = Field(alias="highStressDuration", default=0)

    # Body battery correlation
    body_battery_charged: int | None = Field(alias="bodyBatteryCharged", default=None)
    body_battery_drained: int | None = Field(alias="bodyBatteryDrained", default=None)

    # Stress samples throughout the day
    stress_samples: list[StressSample] = Field(
        alias="stressValuesArray", default_factory=list
    )

    # Raw data
    raw_data: dict[str, Any] | None = Field(default=None, exclude=True)

    @classmethod
    def from_garmin_response(cls, data: dict[str, Any]) -> "StressData":
        """Parse stress data from Garmin API response."""
        
        # Parse stress samples
        samples = []
        raw_samples = data.get("stressValuesArray", [])
        if raw_samples:
            for sample in raw_samples:
                # Samples can be list [ts, val] or dict
                if isinstance(sample, (list, dict)):
                     samples.append(StressSample.from_garmin_response(sample))

        # Helper to get value from either camelCase or snake_case key
        def get_val(camel: str, snake: str, default: Any = None) -> Any:
            return data.get(camel, data.get(snake, default))

        # Timestamps
        start_ts = get_val("startTimestampGMT", "start_timestamp_gmt")
        end_ts = get_val("endTimestampGMT", "end_timestamp_gmt")

        return cls(
            calendar_date=get_val("calendarDate", "calendar_date"),
            start_timestamp=datetime.fromtimestamp(start_ts/1000) if start_ts else None,
            end_timestamp=datetime.fromtimestamp(end_ts/1000) if end_ts else None,
            overall_stress_level=get_val("overallStressLevel", "overall_stress_level"),
            avg_stress_level=get_val("avgStressLevel", "avg_stress_level"),
            max_stress_level=get_val("maxStressLevel", "max_stress_level"),
            rest_stress_duration=get_val("restStressDuration", "rest_stress_duration", 0),
            low_stress_duration=get_val("lowStressDuration", "low_stress_duration", 0),
            medium_stress_duration=get_val("mediumStressDuration", "medium_stress_duration", 0),
            high_stress_duration=get_val("highStressDuration", "high_stress_duration", 0),
            body_battery_charged=get_val("bodyBatteryChargedValue", "body_battery_charged_value"),
            body_battery_drained=get_val("bodyBatteryDrainedValue", "body_battery_drained_value"),
            stress_samples=samples,
            raw_data=data,
        )

    @property
    def rest_duration_hours(self) -> float:
        """Get rest duration in hours."""
        return self.rest_stress_duration / 3600.0

    @property
    def high_stress_hours(self) -> float:
        """Get high stress duration in hours."""
        return self.high_stress_duration / 3600.0
