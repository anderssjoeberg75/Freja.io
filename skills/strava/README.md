# Strava Skill

## What this skill does

The Strava skill integrates account authorization, activity retrieval, and analytics workflows so Freja can summarize your training data and trends.

## Main capabilities

- OAuth connect/disconnect flow
- Token refresh handling
- Recent activity retrieval through tools
- Deterministic fixture-based mock mode for testing
- Command flow for Telegram and chat interactions

## Registered Freja tool

- `get_strava_activities(limit: int = 5)`

## Required configuration

Set these values in `.env` or Freja settings:

- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`
- `STRAVA_REFRESH_TOKEN` (optional bootstrap)
- `STRAVA_ACCESS_TOKEN` (optional local fallback)
- `STRAVA_MOCK=1` (optional test mode)
- `STRAVA_MOCK_FIXTURE` (for example `mixed_run_ride`)

## How to use it via Freja

### Natural language examples

- `Analyze my Strava training from the last 14 days.`
- `Show my latest rides.`
- `How far did I run this week?`

### Command-style examples

- `/strava status`
- `/strava connect`
- `/strava connect <authorization_code>`
- `/strava disconnect`

### Direct tool call (internal)

```json
{
  "tool": "get_strava_activities",
  "args": { "limit": 10 }
}
```

## OAuth callback

Set `STRAVA_REDIRECT_URI` to:

`https://<your-host>/api/integrations/strava/callback`

Strava sends `code` and `state` to this endpoint during authorization.
