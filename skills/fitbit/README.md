# Fitbit Skill

This skill provides a `get_fitbit_health` tool for daily Fitbit data.

## Required settings

- `FITBIT_CLIENT_ID`
- `FITBIT_CLIENT_SECRET`
- `FITBIT_REFRESH_TOKEN`

## Tool

- `get_fitbit_health(activities_limit=5)`
  - Returns daily summary (steps, calories, active-zone minutes, resting HR), sleep summary, and recent activities.
