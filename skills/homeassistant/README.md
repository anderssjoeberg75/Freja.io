# Home Assistant Skill

This skill adds basic Home Assistant REST control in Freja.

## Setup

Set these environment variables:

- `HA_URL` (example: `http://homeassistant.local:8123`)
- `HA_TOKEN` (long-lived access token)

`HA_URL` is normalized automatically, so trailing slash is optional.

## Supported Commands

- `ha list`
- `ha list light`
- `ha get light.kitchen`
- `ha service switch turn_on {"entity_id":"switch.office_lamp"}`
- `ha on switch.office_lamp`
- `ha off switch.office_lamp`
- `ha scene scene.movie_time`

The same command set can be used in Telegram as `/ha ...`.

## Optional curl examples

```bash
curl -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states"
curl -X POST -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id":"switch.office_lamp"}' "$HA_URL/api/services/switch/turn_on"
```
