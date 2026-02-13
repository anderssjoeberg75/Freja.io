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
