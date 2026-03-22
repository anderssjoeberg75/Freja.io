"""Analytics module."""

from pydantic import BaseModel, Field
from typing import Optional
from app.services.tool_registry import registry
from .tools import get_historical_metrics_impl, get_health_trends_impl

class GetHistoricalMetricsArgs(BaseModel):
    metric_name: str = Field(..., description="Namnet på mätvärdet (t.ex. 'weight_kg', 'steps', 'energy_kwh').")
    days: Optional[int] = Field(7, description="Antal dagar bakåt i tiden att hämta.")

class GetHealthTrendsArgs(BaseModel):
    pass

def register_analytics_tools():
    registry.register(
        name="get_historical_metrics",
        description="Hämtar historisk data för hälsa eller energi från databasen.",
        args_schema=GetHistoricalMetricsArgs
    )(get_historical_metrics_impl)
    
    registry.register(
        name="get_health_trends",
        description="Ger en 30-dagars trendanalys för vikt och steg.",
        args_schema=GetHealthTrendsArgs
    )(get_health_trends_impl)
