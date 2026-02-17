# Weather Skill

## What this skill does

The Weather skill gives Freja access to weather forecasts for the configured location. It is intended for daily planning questions and quick forecast checks.

## Registered Freja tool

- `get_weather`

## Required configuration

This skill uses Freja's existing location settings:

- `LATITUDE`
- `LONGITUDE`
- `TIMEZONE` (optional, defaults to `Europe/Stockholm`)

No skill-specific secret is required.

## How to use it via Freja

### Natural language examples

- `What is the weather today?`
- `Will it rain tomorrow morning?`
- `Do I need a jacket this evening?`

### Direct tool call (internal)

```json
{
  "tool": "get_weather",
  "args": {}
}
```

## Notes

- Accuracy depends on the configured provider and location coordinates.
- If coordinates are missing, Freja may return a configuration error.
