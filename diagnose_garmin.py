import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append("/opt/Freja.io")

# Mock the environment to load the .env
from dotenv import load_dotenv
load_dotenv("/opt/Freja.io/.env")

# Set the BASE_DIR to the server path
os.environ["BASE_DIR"] = "/opt/Freja.io"

from app.core.dependencies import get_garmin
from app.core.config import get_credential

async def test_garmin():
    print("--- Garmin Diagnostic ---")
    email = get_credential("GARMIN_EMAIL")
    password = get_credential("GARMIN_PASSWORD")
    
    if not email:
        print("❌ GARMIN_EMAIL is not set.")
    else:
        print(f"✅ GARMIN_EMAIL found: {email[:3]}***")
        
    if not password:
        print("❌ GARMIN_PASSWORD is not set.")
    else:
        print("✅ GARMIN_PASSWORD found.")

    print("\nAttempting to initialize GarminCoach...")
    try:
        garmin = get_garmin()
        if not garmin:
            print("❌ Failed to initialize GarminCoach.")
            return

        print("✅ GarminCoach initialized.")
        
        print("\nAttempting to fetch health report for today...")
        report = garmin.get_health_report()
        
        if "error" in report:
            print(f"❌ Error in health report: {report['error']}")
        else:
            print("✅ Successfully fetched health report!")
            print(f"   Date: {report.get('date')}")
            print(f"   Steps: {report.get('steps')}")
            print(f"   Sleep: {report.get('sleep_hours')}")
            
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_garmin())
