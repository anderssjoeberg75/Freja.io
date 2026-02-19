import sqlite3
import os

DB_PATH = "db/mainframe.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"File {DB_PATH} not found!")
        return

    print("--- Cleaning up Empty Settings ---")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Count before
        cursor.execute("SELECT count(*) FROM settings WHERE value = ''")
        count_before = cursor.fetchone()[0]
        print(f"Found {count_before} empty settings.")

        # Delete empty settings
        cursor.execute("DELETE FROM settings WHERE value = ''")
        conn.commit()
        
        print(f"Deleted {count_before} rows.")
        
        # Verify
        cursor.execute("SELECT count(*) FROM settings")
        count_remaining = cursor.fetchone()[0]
        print(f"Remaining settings: {count_remaining}")
        
        conn.close()

    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    main()
