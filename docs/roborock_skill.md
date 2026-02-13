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
