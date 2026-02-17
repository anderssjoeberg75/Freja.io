# Google Calendar Skill

## What this skill does

The Google Calendar skill lets Freja manage events in your Google Calendar through the Calendar API.

## Main capabilities

- List upcoming events
- Create events
- Update existing events
- Delete events

## Registered Freja tools

- `calendar_list_events`
- `calendar_create_event`
- `calendar_update_event`
- `calendar_delete_event`

## Required configuration

- Valid Google OAuth credentials configured through the skill auth flow.
- Calendar API enabled for the Google project.

## How to use it via Freja

### Natural language examples

- `What is on my calendar today?`
- `Book a meeting tomorrow at 14:00 for 30 minutes.`
- `Move my project sync to 16:00.`
- `Delete the event called Team Retro.`

### Direct tool call example

```json
{
  "tool": "calendar_create_event",
  "args": {
    "summary": "Team Sync",
    "start_time": "2026-02-18T14:00:00",
    "end_time": "30m",
    "description": "Weekly status check",
    "location": "Google Meet"
  }
}
```

## Notes

- Time inputs support ISO datetime and convenience duration formats for end time (`30m`, `1h`).
