import asyncio
import logging
from app.services.chat_service import shared_chat_service

logging.basicConfig(level=logging.INFO)

import uuid

async def main():
    print("--- Starting Strava Test ---", flush=True)
    try:
        print("Importing service...", flush=True)
        # Move import inside to see if import hangs
        from app.services.chat_service import shared_chat_service
        print("Service imported.", flush=True)

        session_id = f"test_strava_{uuid.uuid4().hex[:8]}"
        print(f"Using session ID: {session_id}", flush=True)

        print("--- Testing Native Tool (Strava) ONLY ---", flush=True)
        response_strava = await shared_chat_service.process_message(
            session_id=session_id,
            user_msg="Hämta mina senaste strava aktiviteter."
        )
        print(f"\nResponse:\n{response_strava}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    print("Script started", flush=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted", flush=True)
