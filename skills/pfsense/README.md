# pfSense Skill

## What this skill does

The pfSense skill analyzes firewall and system logs from pfSense through pfrest and returns a summarized incident-oriented report.

## Registered Freja tool

- `analyze_pfsense_logs(limit: int = 200, lookback_minutes: int = 60)`

## Required configuration

Set these values in environment variables or Freja settings:

- `PFSENSE_API_URL`
- `PFSENSE_API_KEY`
- `PFSENSE_VERIFY_TLS` (optional, `true` or `false`)

## How to use it via Freja

### Natural language examples

- `Analyze pfSense logs from the last hour.`
- `Check if there are anomalies in firewall activity.`
- `Generate an incident summary from pfSense.`

### Direct tool call (internal)

```json
{
  "tool": "analyze_pfsense_logs",
  "args": {
    "limit": 300,
    "lookback_minutes": 120
  }
}
```

## Recommended usage

- Use default settings for periodic checks.
- Increase `limit` and `lookback_minutes` for post-incident analysis.
