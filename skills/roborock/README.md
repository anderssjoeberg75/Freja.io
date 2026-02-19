# Roborock Skill

## What this skill does

The Roborock skill connects Freja to your Roborock account so you can manage vacuum devices, trigger cleaning actions, and request map-related data.

## Main capabilities

- Store Roborock account credentials securely
- List account devices and set a default device
- Read status and control cleaning lifecycle
- Retrieve room IDs and clean selected rooms
- View consumables and map metadata
- Generate map image output (`png`)

## Required configuration

Set an encryption key before using credential storage:

```bash
export ROBOROCK_SECRET_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

## Registered Freja tools

- `roborock_configure`
- `roborock_list_devices`
- `roborock_status`
- `roborock_start`
- `roborock_stop`
- `roborock_pause`
- `roborock_dock`
- `roborock_rooms`
- `roborock_clean_rooms`
- `roborock_consumables`
- `roborock_maps`
- `roborock_map_image`

## How to use it via Freja

### Natural language examples

- `Start the robot vacuum.`
- `Send Roborock back to dock.`
- `Clean the kitchen and hallway rooms.`
- `Show my Roborock consumables status.`

### Direct tool call examples

```json
{
  "tool": "roborock_configure",
  "args": {
    "email": "name@example.com",
    "password": "your_password"
  }
}
```

```json
{
  "tool": "roborock_clean_rooms",
  "args": {
    "rooms": [16, 17]
  }
}
```

## Troubleshooting

- `Not logged in` → run `roborock_configure` first.
- `Authentication failed` → verify credentials.
- `Device not found` → re-run configure or pass explicit `device_id`.
