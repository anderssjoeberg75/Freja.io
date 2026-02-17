# Tibber Skill

## What this skill does

The Tibber skill retrieves electricity price and consumption data and returns a practical optimization analysis focused on cost reduction.

## Registered Freja tool

- `get_tibber_energy_analysis(days: int = 7)`

## Required configuration

Set this value in environment variables or Freja settings:

- `TIBBER_API_TOKEN`

## How to use it via Freja

### Natural language examples

- `Analyze my Tibber energy usage for the last 7 days.`
- `How can I reduce my electricity costs this week?`
- `Show peak-hour consumption patterns for this month.`

### Direct tool call (internal)

```json
{
  "tool": "get_tibber_energy_analysis",
  "args": {
    "days": 14
  }
}
```

## Recommended ranges

- `days: 7` for short-term operational advice.
- `days: 14` or `days: 30` for trend analysis.
