#!/usr/bin/env python3
import asyncio
import os
import sys

# Auto-activate venv if running with system python
if sys.prefix == sys.base_prefix:
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "bin", "python")
    if os.path.exists(venv_python):
        print(f"🔄 Re-executing with venv: {venv_python}")
        os.execv(venv_python, [venv_python] + sys.argv)

from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

print("DEBUG: Importing database...", flush=True)
from app.core.database import init_db, get_db_settings
print("DEBUG: Importing telegram_service...", flush=True)
from app.services.telegram_service import init_telegram_service
print("DEBUG: Importing proactive_service...", flush=True)
from app.services.proactive_service import ProactiveService
print("DEBUG: Importing config...", flush=True)
from app.core.config import settings as app_settings
print("DEBUG: Imports done.", flush=True)

async def main():
    print("[-] Initializing Database...")
    init_db()
    
    print("[-] Loading Settings from DB...")
    db_settings = get_db_settings()
    print(f"DEBUG: Available keys: {list(db_settings.keys())}")
    
    bot_token = db_settings.get("TELEGRAM_BOT_TOKEN")
    chat_id_str = db_settings.get("TELEGRAM_CHAT_ID")
    
    print(f"DEBUG: Found token: {bool(bot_token)}, chat_id: {bool(chat_id_str)}")

    if not bot_token or not chat_id_str:
        print("❌ Telegram not configured in database!")
        # Fallback to env just in case
        if not bot_token and app_settings.TELEGRAM_BOT_TOKEN:
             bot_token = app_settings.TELEGRAM_BOT_TOKEN
             print("DEBUG: Using env token")
        if not chat_id_str and app_settings.TELEGRAM_CHAT_ID:
             chat_id_str = app_settings.TELEGRAM_CHAT_ID
             print("DEBUG: Using env chat_id")
        
        if not bot_token or not chat_id_str:
            return

    print("[-] Initializing Telegram Service (Mocked transport)...")
    # minimal mock callback
    async def dummy_callback(msg):
        return "ack"
        
    ts = init_telegram_service(dummy_callback)
    ts.bot_token = bot_token
    ts.chat_ids = [cid.strip() for cid in chat_id_str.split(",") if cid.strip()]
    
    # We need to mock the bot instance because send_message uses self.application.bot.send_message
    ts.application = MagicMock()
    ts.application.bot.send_message = MagicMock(side_effect=lambda chat_id, text, parse_mode=None: print(f"🚀 [MOCK SEND] To {chat_id}:\n{text}"))
    
    print("[-] Initializing Proactive Service...")
    mock_sio = MagicMock()
    ps = ProactiveService(mock_sio)
    
    print("[-] Triggering Morning Briefing...")
    # Hook into the shared_chat_service to avoid needing a real LLM for this test if possible?
    # actually send_morning_briefing calls shared_chat_service.run_proactive_task which calls the LLM.
    # If we want a real briefing we need the real LLM service.
    # app/services/chat_service.py -> shared_chat_service
    # It should work if the key is in env or settings.
    
    await ps.send_morning_briefing()
    print("[-] Done.")

if __name__ == "__main__":
    asyncio.run(main())
