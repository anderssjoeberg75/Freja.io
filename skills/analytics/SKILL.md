# Analytics Skill

This skill provides tools for analyzing historical health and energy data stored in the `metrics` table.

## Tools

- **get_historical_metrics(metric_name, days=7)**: Retrieves a list of data points for a specific metric over a given period. Supported metrics include:
    - `weight_kg` (vikt)
    - `steps` (steg)
    - `body_battery_now` (body battery)
    - `energy_kwh` (el/energi)
    - `energy_cost` (elkostnad)
    - `sleep_hours` (sömn)
    - `resting_heart_rate` (vilopuls)
- **get_health_trends()**: Provides a 30-day trend analysis for weight and steps.

## Persistence

Data is automatically persisted to the `metrics` table by the `ProactiveService` during the daily morning briefing. This ensures a consistent time-series record for all connected services (Garmin, Strava, Withings, Fitbit, and Tibber).
