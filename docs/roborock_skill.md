# Roborock Skill Integration

This document describes how the `roborock` skill is wired into Freja.io.

- Skill package path: `skills/roborock`.
- Auto-discovery: handled by `skills/_core/skill_loader.py`.
- User persistence: SQLite table `roborock_credentials` in the shared DB.

## Database schema

`roborock_credentials` stores one credential set per Freja user:

- `user_id` (TEXT, PK)
- `email` (TEXT)
- `password_encrypted` (TEXT)
- `device_id` (TEXT, nullable)
- `device_name` (TEXT, nullable)
- `device_model` (TEXT, nullable)
- `created_at` / `updated_at`

## Runtime requirement

You must set `ROBOROCK_SECRET_KEY` to a valid Fernet key.

## Smoke-test checklist

1. Configure credentials with `roborock_configure`.
2. Verify default device is persisted.
3. Call `roborock_list_devices`.
4. Call control tools (`status`, `start`, `pause`, `dock`).
5. Call `roborock_rooms` and `roborock_clean_rooms`.
6. Call `roborock_consumables`, `roborock_maps`, and `roborock_map_image`.

## Chat usage examples

Freja can call Roborock tools from natural language prompts such as:

- "Starta dammsugaren" → maps to `roborock_start`.
- "Pausa dammsugaren" → maps to `roborock_pause`.
- "Skicka dammsugaren till dockan" → maps to `roborock_dock`.

## Required environment variables

- `ROBOROCK_SECRET_KEY`: Fernet key used to encrypt credentials in SQLite.
- `USER_ID` (optional): Freja user partition used for credential lookup. Defaults to the configured app user.

Generate a key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
