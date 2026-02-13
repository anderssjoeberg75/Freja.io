
import sqlite3
import os

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "db", "mainframe.db")

print(f"Connecting to DB at {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check current value
c.execute("SELECT value FROM settings WHERE key='WEB_FALLBACK_PROVIDER'")
row = c.fetchone()
print(f"Current WEB_FALLBACK_PROVIDER: {row[0] if row else 'NOT SET'}")

# Update
print("Updating to 'serpapi'...")
c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('WEB_FALLBACK_PROVIDER', 'serpapi')")
conn.commit()

# Verify
c.execute("SELECT value FROM settings WHERE key='WEB_FALLBACK_PROVIDER'")
row = c.fetchone()
print(f"New WEB_FALLBACK_PROVIDER: {row[0] if row else 'NOT SET'}")

conn.close()
