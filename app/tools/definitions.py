from typing import Optional
from pydantic import BaseModel, Field

class RunPythonCode(BaseModel):
    """
    Executes Python code in a secure sandboxed environment.
    Use this for calculations, data processing, or logic that requires programming.
    """
    code: str = Field(..., description="The valid Python code to execute.")

class WebSearch(BaseModel):
    """
    Searches the internet for information.
    Use this when you need current information, facts about recent events, or knowledge outside your training data.
    """
    query: str = Field(..., description="The search query.")

class GetGarminHealth(BaseModel):
    """
    Retrieves Garmin health data (steps, sleep, heart rate, body battery) for a specific date.
    Use this when the user asks about their health, training status, or sleep.
    """
    date_str: str = Field(..., description="The date to fetch data for in YYYY-MM-DD format. Defaults to today if not specified.")

class GetStravaActivity(BaseModel):
    """
    Retrieves recent activities from Strava.
    Use this when the user asks about their recent workouts, runs, or rides recorded on Strava.
    """
    limit: int = Field(5, description="The maximum number of activities to retrieve. Defaults to 5.")


class GetWeather(BaseModel):
    """
    Retrieves weather data for the configured home coordinates.
    Requires LATITUDE and LONGITUDE settings.
    """
    pass


class RoborockConfigure(BaseModel):
    """Configure Roborock credentials and optional default device."""

    email: str = Field(..., description="Roborock/Xiaomi account e-mail address.")
    password: str = Field(..., description="Roborock/Xiaomi account password.")
    device_id: Optional[str] = Field(
        None,
        description="Optional default Roborock device identifier. If omitted, first device is auto-selected.",
    )


class RoborockDeviceInput(BaseModel):
    """Optional device selector used by most Roborock tools."""

    device_id: Optional[str] = Field(
        None,
        description="Device identifier. Uses configured default when omitted.",
    )


class RoborockCleanRoomsInput(BaseModel):
    """Room-cleaning input supporting either explicit list or CSV values."""

    device_id: Optional[str] = Field(
        None,
        description="Device identifier. Uses configured default when omitted.",
    )
    rooms: list[int] | str = Field(
        ...,
        description="Room/segment IDs either as integer list or comma-separated string (for example '16,17').",
    )


class RoborockMapImageInput(BaseModel):
    """Map rendering input for output format control."""

    device_id: Optional[str] = Field(
        None,
        description="Device identifier. Uses configured default when omitted.",
    )
    output_format: str = Field(
        "png",
        description="Requested map image format. Currently only 'png' is supported.",
    )
