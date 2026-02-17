---
name: pfsense-log-monitor
description: Use this skill when a user wants to monitor pfSense logs through pfrest, generate incident reports, or detect anomalous activity.
---

# pfSense Log Monitor Skill

## Purpose
Use pfrest endpoints to read pfSense logs, summarize normal behavior, and produce alerts when unusual patterns occur.

## Configuration
Before using tools, verify these environment variables:

- `PFSENSE_API_URL` (example: `https://pfsense.local`)
- `PFSENSE_API_KEY`
- `PFSENSE_VERIFY_TLS` (`true` or `false`, optional)

## Workflow
1. Call `analyze_pfsense_logs` with a relevant `limit` and `lookback_minutes`.
2. Return the report in Swedish to the user, but keep technical labels and alert text in English.
3. If anomalies are present, include clear next steps (for example: check firewall rules, VPN auth attempts, WAN health).
4. If no anomalies are present, state that monitoring should continue and suggest running periodic checks.

## Recommended defaults
- `limit: 200`
- `lookback_minutes: 60`

Increase `limit` to 500+ for incident analysis.
