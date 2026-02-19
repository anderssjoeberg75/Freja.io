import sys
import os

# Auto-activate venv if running with system python
if sys.prefix == sys.base_prefix:
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "bin", "python")
    if os.path.exists(venv_python):
        print(f"🔄 Re-executing with venv: {venv_python}")
        os.execv(venv_python, [venv_python] + sys.argv)

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.core.database import get_db_settings
    
    print("Fetching settings from database...")
    settings = get_db_settings()
    
    if not settings:
        print("No settings found in database!")
        sys.exit(1)
        
    print(f"Found {len(settings)} settings.")
    
    # Write to .env
    with open(".env", "w") as f:
        for key, value in settings.items():
            # Only write keys that have values, or write all?
            # User wants to sync DB to env.
            if value:
                f.write(f"{key}={value}\n")
                
    print(f"Successfully wrote {len(settings)} settings to .env")
    
    # Verify specific keys
    if "GOOGLE_API_KEY" in settings and settings["GOOGLE_API_KEY"]:
        print("GOOGLE_API_KEY is present.")
    else:
        print("WARNING: GOOGLE_API_KEY is missing or empty in DB!")

    if "OPENAI_API_KEY" in settings and settings["OPENAI_API_KEY"]:
        print("OPENAI_API_KEY is present.")
    else:
        print("WARNING: OPENAI_API_KEY is missing or empty in DB!")

except Exception as e:
    print(f"Error syncing settings: {e}")
    sys.exit(1)
