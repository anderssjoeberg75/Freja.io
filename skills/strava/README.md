# Freja.io Strava Skill

## What this module does
This skill provides a modular Strava integration for Freja.io with:
- OAuth connect and refresh-token based authentication.
- Athlete profile/stats fetch + activity pagination.
- Rate-limit handling with retry logic.
- Activity normalization + per-user cache.
- Deterministic analytics pipeline used by Telegram command handling.
- Tool registration for `get_strava_activities` via Freja's shared tool registry.

## Environment variables
Configure these in `.env` or via Freja settings:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI` (for callback endpoint)
- `STRAVA_REFRESH_TOKEN` (optional bootstrap fallback)
- `STRAVA_ACCESS_TOKEN` (optional local dev fallback)
- `STRAVA_MOCK=1` (optional fixture mode)
- `STRAVA_MOCK_FIXTURE=mixed_run_ride` (or `run_only_hr`)

## Telegram usage
- `/strava status`
- `/strava connect`
- `/strava connect <code>` for manual exchange fallback
- `/strava disconnect`
- `analysera min strava senaste 30 dagar`
- `analysera min strava 7 dagar run`

## OAuth callback
Set `STRAVA_REDIRECT_URI` to:
`https://<your-host>/api/integrations/strava/callback`

Strava will call this endpoint with `code` and `state`.
The `state` value stores Telegram user/chat ID so token storage stays per user.

## Test in mock mode
Run deterministic self-test with fixture data:
```bash
STRAVA_MOCK=1 STRAVA_MOCK_FIXTURE=mixed_run_ride python scripts/strava_self_test.py
STRAVA_MOCK=1 STRAVA_MOCK_FIXTURE=run_only_hr python scripts/strava_self_test.py
```
