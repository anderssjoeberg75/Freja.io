"""Base model for Garmin data."""

from datetime import datetime, date
from typing import Any, TypeVar, Generic
from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="BaseGarminModel")

class BaseGarminModel(BaseModel):
    """Base model for all Garmin data."""
    
    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_garmin_response(cls: type[T], data: dict[str, Any]) -> T:
        """Create model from Garmin API response."""
        return cls(**data)
