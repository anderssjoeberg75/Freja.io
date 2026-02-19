# Garmin Skill

## What this skill does

The Garmin skill integrates Garmin Connect health data into Freja. It is designed for quick daily snapshots such as steps, sleep, resting heart rate, and energy-related metrics.

## Registered Freja tool

- `get_garmin_health(date: str | None = None)`
  - Fetches Garmin health metrics for a specific date (or the latest available day).

## Required configuration

Set credentials in environment variables or Freja settings:

- `GARMIN_EMAIL`
- `GARMIN_PASSWORD`

## How to use it via Freja

### Natural language examples

- `How did I sleep last night?`
- `Show my Garmin health stats for today.`
- `What was my resting heart rate yesterday?`

### Direct tool call (internal)

```json
{
  "tool": "get_garmin_health",
  "args": { "date": "2026-02-16" }
}
```

## Notes

- If credentials are missing, Freja will return a configuration error.
- Date format should be `YYYY-MM-DD` when provided explicitly.
