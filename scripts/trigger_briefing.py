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
    db_settings = await get_db_settings()
    print(f"DEBUG: Available keys: {list(db_settings.keys())}")
    
    from app.core.config import get_credential
    bot_token = get_credential("TELEGRAM_BOT_TOKEN")
    chat_id_str = get_credential("TELEGRAM_CHAT_ID")
    
    print(f"DEBUG: Found token: {bool(bot_token)}, chat_id: {bool(chat_id_str)}")

    if not bot_token or not chat_id_str:
        print("❌ Telegram not configured! Cannot send briefing.")
        return

    print("[-] Initializing Telegram Service (Real)...")
    async def dummy_callback(msg):
        return "ack"
        
    ts = init_telegram_service(dummy_callback)
    ts.bot_token = bot_token
    ts.chat_ids = [cid.strip() for cid in chat_id_str.split(",") if cid.strip()]
    
    # Mock bot to prevent actual Telegram delivery during test
    ts.application = MagicMock()

    async def mock_send_message(chat_id, text, parse_mode=None):
        print(f"🚀 [MOCK SEND_MESSAGE] To {chat_id}:\n{text[:300]}...")

    async def mock_send_document(chat_id, document, caption=None):
        print(f"📎 [MOCK SEND_DOCUMENT] To {chat_id}: {caption}")

    ts.application.bot.send_message = mock_send_message
    ts.application.bot.send_document = mock_send_document
    
    print("[-] Initializing Proactive Service...")
    mock_sio = MagicMock()
    ps = ProactiveService(mock_sio)
    
    print("[-] Triggering Morning Briefing (calling LLM)...")
    await ps.send_morning_briefing()
    print("[-] Done.")

if __name__ == "__main__":
    asyncio.run(main())
