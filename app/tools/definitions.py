from typing import Optional, Union, List
import datetime as _dt
from pydantic import BaseModel, Field


class RunPythonCode(BaseModel):
    """Execute Python code in a secure sandboxed environment."""

    code: str = Field(..., description="The valid Python code to execute.")


class WebSearch(BaseModel):
    """Search the internet for information."""

    query: str = Field(..., description="The search query.")


class GetGarminHealth(BaseModel):
    """Retrieve daily Garmin health metrics (NOT workouts/träningspass)."""

    date_str: str = Field(
        default_factory=lambda: _dt.date.today().isoformat(),
        description="Datumet att hämta data för i formatet YYYY-MM-DD. Om inte angivet används dagens datum.",
    )


class GetStravaActivity(BaseModel):
    """Retrieve recent workout activities (träningspass) from Strava."""

    limit: int = Field(5, description="The maximum number of activities to retrieve. Defaults to 5.")


class GetWeather(BaseModel):
    """Retrieve weather data for the configured home coordinates."""

    pass


class GetWithingsHealth(BaseModel):
    """Retrieve Withings health and body-composition data for the current user."""

    pass


class RoborockConfigure(BaseModel):
    """Configure Roborock integration credentials and optional default device."""

    email: str = Field(..., description="Roborock account e-mail.")
    password: str = Field(..., description="Roborock account password.")
    device_id: Optional[str] = Field(None, description="Optional device id to set as default.")


class RoborockDeviceInput(BaseModel):
    """Optional target device for Roborock commands."""

    device_id: Optional[str] = Field(None, description="Target Roborock device id.")


class RoborockCleanRoomsInput(BaseModel):
    """Room cleaning input for Roborock."""

    device_id: Optional[str] = Field(None, description="Target Roborock device id.")
    rooms: Union[List[int], str] = Field(
        ...,
        description="Room ids as list (e.g. [16,17]) or CSV string (e.g. '16,17').",
    )


class RoborockMapImageInput(BaseModel):
    """Map image export input for Roborock."""

    device_id: Optional[str] = Field(None, description="Target Roborock device id.")
    output_format: str = Field("png", description="Output format. Currently only png is supported.")


class AnalyzePfSenseLogs(BaseModel):
    """Analyze pfSense logs and return a report with anomaly warnings."""

    limit: int = Field(200, description="Number of log lines to sample from pfSense.")
    lookback_minutes: int = Field(60, description="Time window in minutes used to identify recent spikes.")


class GetTibberEnergyAnalysis(BaseModel):
    """Analyze Tibber hourly energy consumption and electricity prices."""

    days: int = Field(7, description="Number of days to analyze (1-30).")
