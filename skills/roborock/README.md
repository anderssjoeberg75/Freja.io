# Roborock skill

This skill adds Roborock vacuum controls to Freja.io.

## Features

- Configure Roborock account credentials securely (encrypted password in DB).
- List available devices and auto-save default device on configure.
- Vacuum controls: status, start, stop, pause, dock.
- Room cleaning controls: list rooms and clean selected rooms.
- Consumables and map endpoints.
- Map image endpoint (`png`) using Freja tool response payload.

## Security

Set an encryption key in environment before using the skill:

```bash
export ROBOROCK_SECRET_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

The password is encrypted with this key before being stored in SQLite.

## Tool usage examples

1. Configure:

```json
{"tool": "roborock_configure", "args": {"email": "name@example.com", "password": "secret"}}
```

2. List devices:

```json
{"tool": "roborock_list_devices", "args": {}}
```

3. Start cleaning:

```json
{"tool": "roborock_start", "args": {}}
```

4. Clean rooms 16 and 17:

```json
{"tool": "roborock_clean_rooms", "args": {"rooms": [16, 17]}}
```

## Troubleshooting

- `Not logged in`: run `roborock_configure` first.
- `Authentication failed`: verify email/password.
- `Device not found`: set a valid `device_id` or re-run configure.
- `Roborock dependency not installed`: install python-roborock in runtime.

## Manual smoke test

1. Export `ROBOROCK_SECRET_KEY`.
2. Restart Freja service.
3. Run `roborock_configure` with valid account.
4. Run `roborock_list_devices`.
5. Run `roborock_status` for default or explicit `device_id`.
6. Run `roborock_start` then `roborock_pause` then `roborock_dock`.
7. Run `roborock_rooms` and `roborock_clean_rooms` with one room ID.
