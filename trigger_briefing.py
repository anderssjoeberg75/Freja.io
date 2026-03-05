import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from app.core.database import init_db
init_db()

from app.services.telegram_service import init_telegram_service
from app.services.proactive_service import init_proactive_service

async def main():
    async def dummy_callback(*args): return "ok"
    # Ladda in tjänsterna på riktigt så vi skickar till Telegram och inte bara printar
    tel = init_telegram_service(dummy_callback)
    await tel.start()
    
    proactive = init_proactive_service(None)
    print("Skickar riktig briefing...")
    await proactive.send_morning_briefing()
    print("Briefing skickad!")
    
    await tel.stop()

if __name__ == "__main__":
    asyncio.run(main())
