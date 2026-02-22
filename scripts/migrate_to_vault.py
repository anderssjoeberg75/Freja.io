#!/usr/bin/env python3
import asyncio
import os
import sys

# Ensure the app module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_settings
from app.core.settings_schema import SETTINGS_SCHEMA
from app.core.vault import save_vault_secret

async def migrate():
    print("Starting migration from SQLite to Vault...")
    
    settings = await get_db_settings()
    if not settings:
        print("No settings found in the database. Nothing to migrate.")
        return

    migrated_count = 0
    failed_count = 0

    secret_keys = {item.key for item in SETTINGS_SCHEMA if item.type == "password"}

    for key, value in settings.items():
        if key in secret_keys and value:
            # It's a populated secret!
            print(f"Migrating secret: {key}")
            success = save_vault_secret(key, value)
            if success:
                migrated_count += 1
            else:
                print(f"  -> Failed to migrate {key}")
                failed_count += 1

    print("--- Migration Summary ---")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Failed to migrate: {failed_count}")
    
    if migrated_count > 0:
        print("\nNote: The old secrets are STILL in the database (for safety backup).")
        print("You may manually delete them later or clear those columns if needed.")

if __name__ == "__main__":
    asyncio.run(migrate())
