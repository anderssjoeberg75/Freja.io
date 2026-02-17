# Withings Skill

## What this skill does

The Withings skill lets Freja fetch body and health metrics from Withings devices, such as weight and body composition.

## Registered Freja tool

- `get_withings_health`

## Main data points

- Weight
- Body fat percentage
- Muscle mass (when available)

## Required configuration

Set these values in environment variables or Freja settings:

- `WITHINGS_CLIENT_ID`
- `WITHINGS_CLIENT_SECRET`
- `WITHINGS_REDIRECT_URI`
- `WITHINGS_REFRESH_TOKEN` (required after OAuth authorization)

## How to use it via Freja

### Natural language examples

- `What is my latest weight from Withings?`
- `Show my body composition.`
- `Give me my most recent Withings health report.`

### Direct tool call (internal)

```json
{
  "tool": "get_withings_health",
  "args": {}
}
```

## OAuth callback

Configure redirect URI as:

`https://<your-host>/api/integrations/withings/callback`
