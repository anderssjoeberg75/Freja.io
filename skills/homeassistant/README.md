# Home Assistant Skill

## What this skill does

The Home Assistant skill lets Freja control entities and scenes through the Home Assistant REST API. It supports both tool-based calls and command-style chat usage.

## Supported capabilities

- List entities by domain
- Read state of a specific entity
- Turn entities on/off
- Call arbitrary Home Assistant services
- Activate scenes

## Required configuration

Set these values in environment variables or Freja settings:

- `HA_URL` (example: `http://homeassistant.local:8123`)
- `HA_TOKEN` (long-lived access token)

## How to use it via Freja

### Command-style usage

- `ha list`
- `ha list light`
- `ha get light.kitchen`
- `ha on switch.office_lamp`
- `ha off switch.office_lamp`
- `ha scene scene.movie_time`
- `ha service switch turn_on {"entity_id":"switch.office_lamp"}`

In Telegram, use the same commands prefixed with `/ha`.

### Natural language examples

- `Turn on the kitchen light.`
- `List all switches in Home Assistant.`
- `Activate my movie scene.`

## Operational guidance

- Keep entity IDs exact (for example `light.kitchen_ceiling`).
- If a command fails, verify token validity and API URL reachability.
