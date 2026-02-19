import sqlite3
import os
import sys

# Auto-activate venv if running with system python
if sys.prefix == sys.base_prefix:
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "bin", "python")
    if os.path.exists(venv_python):
        print(f"🔄 Re-executing with venv: {venv_python}")
        os.execv(venv_python, [venv_python] + sys.argv)

DB_PATH = "db/mainframe.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"File {DB_PATH} not found!")
        return

    print("--- Database Dump ---")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found.")
            return

        for table in tables:
            table_name = table[0]
            print(f"\n--- Table: {table_name} ---")
            
            cursor.execute(f"SELECT count(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")

            if table_name == "settings":
                 print("-" * 20)
                 cursor.execute(f"SELECT * FROM {table_name}")
                 rows = cursor.fetchall()
                 for row in rows:
                     print(f"{row}")
            elif table_name == "prompts":
                 print("-" * 20)
                 cursor.execute(f"SELECT key FROM {table_name}")
                 rows = cursor.fetchall()
                 for row in rows:
                     print(f"Key: {row[0]}")
            elif table_name == "history":
                 print("-" * 20)
                 cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 5")
                 rows = cursor.fetchall()
                 for row in rows:
                     print(f"{row}")
            else:
                 print("(Skipping full content)")

        conn.close()

    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    main()
