# Freja Skills

This directory contains Freja's pluggable skills. A skill adds one or more tools (function calls) and, in some cases, direct command handlers.

## How skills are loaded

- Skills are discovered from `skills/*` packages and registered through the shared tool registry during startup.
- Most skills expose tools through a `register_tools(registry)` function.
- Some skills also provide chat command handlers (for example Home Assistant and Strava command flows).

## How to invoke skills via Freja

You can trigger skills in two ways:

1. **Natural language in chat (recommended)**
   - Example: `Analyze my Strava activities from the last 7 days.`
   - Example: `Turn on the office lamp in Home Assistant.`

2. **Explicit command syntax (skills that support commands)**
   - Home Assistant: `ha list light`, `ha on light.office`
   - Strava: `/strava status`, `/strava connect`

Freja decides when to call the underlying tool automatically.

## Skill index

- `codex` – code execution, Git operations, and codebase auditing.
- `garmin` – health snapshot from Garmin Connect.
- `fitbit` – daily Fitbit activity, sleep, and heart-rate summaries.
- `google_calendar` – list/create/update/delete calendar events.
- `homeassistant` – smart-home control via Home Assistant API.
- `pfsense` – firewall/system log analysis via pfrest.
- `roborock` – Roborock vacuum control and map access.
- `strava` – Strava activity retrieval and analytics flow.
- `tibber` – electricity usage and cost analysis.
- `weather` – weather forecasts.
- `wordpress` – publish or draft blog posts via WordPress REST API.
- `withings` – body composition and health metrics.

## Adding a new skill

1. Create a new folder under `skills/<name>/`.
2. Add `__init__.py` and `tools.py` (or command handlers if needed).
3. Register tools via `register_tools(registry)`.
4. Document configuration and invocation in `skills/<name>/README.md`.
5. Restart Freja and test through chat.
