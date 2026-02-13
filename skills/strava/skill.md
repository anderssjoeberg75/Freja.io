# Skill: Strava for Freja.io

## Purpose
Provide Strava-specific capabilities in a reusable skill module instead of hardcoded flow logic.

## Setup
1. Configure `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, and `STRAVA_REDIRECT_URI`.
2. Start Freja backend.
3. In Telegram, run `/strava connect`.
4. Complete OAuth in browser.
5. Optional manual fallback: `/strava connect <code>`.

## Commands
- `/strava status` → show connection status and token metadata.
- `/strava connect` → generate auth URL.
- `/strava disconnect` → remove stored tokens and cache.
- `analysera min strava ...` → run analytics report.

## Analysis options
Text parser supports period and type filters:
- Period: `7`, `30`, `90` days.
- Type filter keywords: `run`, `ride`, `walk`.

## Output contract
Telegram responses are always structured as:
1. `Svar:`
2. `Sammanfattning`
3. `Trender`
4. `Highlights`
5. `Rekommendationer`

## Mock mode
Use deterministic fixtures for local verification:
- `STRAVA_MOCK=1`
- `STRAVA_MOCK_FIXTURE=mixed_run_ride` or `run_only_hr`

## Internal modules
- `storage.py`: token/cache SQLite layer.
- `strava_auth.py`: OAuth URL + code exchange + token refresh.
- `strava_client.py`: endpoint client + retry + normalization.
- `strava_analytics.py`: deterministic coaching analytics.
- `strava_commands.py`: Telegram parsing + formatting.
