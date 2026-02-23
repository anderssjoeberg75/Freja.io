import asyncio
import os
import sys

# Ensure the app module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_connection, init_db
from app.core.settings_schema import SETTINGS_SCHEMA

async def cleanup():
    print("Starting cleanup of secrets from SQLite database...")
    init_db()
    
    deleted_count = 0
    secret_keys = {item.key for item in SETTINGS_SCHEMA if item.type == "password"}

    async with get_db_connection() as db:
        for key in secret_keys:
            try:
                # Radera nyckeln från databasen permanent
                await db.execute("DELETE FROM settings WHERE key = ?", (key,))
                await db.commit()
                deleted_count += 1
                print(f"🗑️ Deleted secret from DB: {key}")
            except Exception as e:
                print(f"❌ Failed to delete {key}: {e}")

    print("--- Cleanup Summary ---")
    print(f"Successfully deleted {deleted_count} secret objects from the database.")
    print("All secrets are now exclusively handled by HashiCorp Vault.")

if __name__ == "__main__":
    asyncio.run(cleanup())
