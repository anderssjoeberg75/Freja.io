import asyncio
import logging
from app.services.chat_service import shared_chat_service

logging.basicConfig(level=logging.INFO)

async def main():
    print("--- Testing Native Tool (Python) ---")
    response = await shared_chat_service.process_message(
        session_id="test_native_tool",
        user_msg="Calculate 123 * 456 using python code."
    )
    print(f"\nResponse:\n{response}")

    print("\n--- Testing Native Tool (Web Search) ---")
    response_web = await shared_chat_service.process_message(
        session_id="test_native_tool_web",
        user_msg="Who directed the movie Inception?"
    )
    print(f"\nResponse:\n{response_web}")

    print("\n--- Testing Native Tool (Strava) ---")
    response_strava = await shared_chat_service.process_message(
        session_id="test_native_tool_strava",
        user_msg="Hämta mina senaste strava aktiviteter."
    )
    print(f"\nResponse:\n{response_strava}")

if __name__ == "__main__":
    asyncio.run(main())
