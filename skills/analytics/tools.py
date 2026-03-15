import logging
from typing import Optional
from app.core.database import get_metrics

logger = logging.getLogger(__name__)

async def get_historical_metrics_impl(metric_name: str, days: int = 7) -> str:
    """
    Hämtar historisk data för ett specifikt mätvärde.
    Exempel på mätvärden: 'weight_kg', 'steps', 'body_battery_now', 'energy_kwh'.
    """
    logger.info(f"Fetching historical metrics for {metric_name} over {days} days")
    
    # Map common aliases to internal metric names
    mapping = {
        "vikt": "weight_kg",
        "steg": "steps",
        "body battery": "body_battery_now",
        "energi": "energy_kwh",
        "el": "energy_kwh",
        "kostnad": "energy_cost",
        "sömn": "sleep_hours",
        "vilopuls": "resting_heart_rate"
    }
    
    internal_name = mapping.get(metric_name.lower(), metric_name)
    rows = await get_metrics(internal_name, days=days, limit=100)
    
    if not rows:
        return f"Ingen historisk data hittades för '{metric_name}' de senaste {days} dagarna."
        
    result = [f"Historik för {metric_name} ({days} dagar):"]
    for row in rows:
        ts = row['timestamp']
        val = row['value']
        unit = row['unit'] or ""
        result.append(f"- {ts}: {val} {unit}")
        
    return "\n".join(result)

async def get_health_trends_impl() -> str:
    """
    Ger en sammanfattning av trender för vikt och steg de senaste 30 dagarna.
    """
    weight_rows = await get_metrics("weight_kg", limit=30)
    steps_rows = await get_metrics("steps", limit=30)
    
    summary = ["Hälsotrender (Senaste 30 dagarna):"]
    
    if weight_rows:
        latest_w = weight_rows[0]['value']
        earliest_w = weight_rows[-1]['value']
        diff = latest_w - earliest_w
        trend = "ökat" if diff > 0 else "minskat"
        summary.append(f"- Vikt: Har {trend} med {abs(diff):.1f} kg (från {earliest_w:.1f} till {latest_w:.1f}).")
    else:
        summary.append("- Vikt: Ingen data tillgänglig.")
        
    if steps_rows:
        avg_steps = sum(r['value'] for r in steps_rows) / len(steps_rows)
        summary.append(f"- Steg: Snittar {int(avg_steps)} steg per dag.")
    else:
        summary.append("- Steg: Ingen data tillgänglig.")
        
    return "\n".join(summary)
