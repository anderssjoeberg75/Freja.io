"""
Telegram Bot Service for Freja
Handles bidirectional messaging via Telegram.
"""
import asyncio
import logging
import re
import time
from typing import Optional, Callable
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app.core.database import get_db_settings

logger = logging.getLogger(__name__)

# Global instance
telegram_service: Optional['TelegramService'] = None

# Rate limiting
_last_message_time: float = 0
RATE_LIMIT_SECONDS = 1.0


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters to prevent parse errors."""
    # Characters that need escaping in Telegram Markdown
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


class TelegramService:
    """Telegram bot service for receiving and sending messages."""
    
    def __init__(self, on_message: Callable[[str], asyncio.Future]):
        """
        Initialize Telegram service.
        
        Args:
            on_message: Async callback that receives user message and returns AI response.
        """
        self.on_message = on_message
        self.application: Optional[Application] = None
        self.bot_token: Optional[str] = None
        self.chat_id: Optional[str] = None
        self._running = False
    
    async def start(self):
        """Start the Telegram bot polling."""
        settings = get_db_settings()
        self.bot_token = settings.get("TELEGRAM_BOT_TOKEN", "").strip()
        
        chat_id_str = settings.get("TELEGRAM_CHAT_ID", "").strip()
        self.chat_ids = [cid.strip() for cid in chat_id_str.split(",") if cid.strip()]
        
        if not self.bot_token:
            logger.warning("Telegram: No bot token configured, service disabled")
            return
        
        if not self.chat_ids:
            logger.warning("Telegram: No chat ID configured, will accept all chats (WARNING)")
        
        try:
            # Build application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self._handle_message
            ))
            
            # Initialize and start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            self._running = True
            logger.info(f"Telegram bot started (Allowed Chat IDs: {self.chat_ids})")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
    
    async def stop(self):
        """Stop the Telegram bot."""
        if self.application and self._running:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                self._running = False
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")
    
    @property
    def primary_chat_id(self) -> Optional[str]:
        """Returns the first configured chat ID."""
        return self.chat_ids[0] if self.chat_ids else None

    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """
        Send a message to resolving chat IDs.
        
        Args:
            text: Message to send
            chat_id: Specific chat ID to send to. If None, sends to ALL configured IDs.
            
        Returns:
            True if sent successfully to at least one chat
        """
        if not self.application or not self.chat_ids:
            logger.warning("Telegram: Cannot send message, not configured")
            return False
        
        target_ids = [chat_id] if chat_id else self.chat_ids
        success = False
        
        for cid in target_ids:
            try:
                await self.application.bot.send_message(
                    chat_id=int(cid),
                    text=text,
                    parse_mode="Markdown"
                )
                success = True
            except Exception as e:
                logger.error(f"Telegram send error for {cid}: {e}")
        
        return success
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)
        logger.info(f"Telegram /start from chat {chat_id}")
        
        welcome_msg = f"🤖 *Freja Online*\n\nDitt Chat ID: `{chat_id}`\n\n"
        
        if self.chat_ids and chat_id not in self.chat_ids:
            welcome_msg += "⛔ Du är inte behörig att använda denna bot."
        else:
            welcome_msg += "✅ Du är inloggad! Skriv ett meddelande så svarar jag."
            
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages."""
        global _last_message_time
        
        chat_id = str(update.effective_chat.id)
        
        # Check if from authorized chat
        if self.chat_ids and chat_id not in self.chat_ids:
            logger.warning(f"Telegram: Unauthorized chat {chat_id}")
            await update.message.reply_text("⛔ Obehörig användare.")
            return
        
        # Rate limiting
        current_time = time.time()
        if current_time - _last_message_time < RATE_LIMIT_SECONDS:
            await update.message.reply_text("⏳ Vänta lite innan du skickar nästa meddelande.")
            return
        _last_message_time = current_time
        
        user_message = update.message.text
        logger.info(f"Telegram message: {user_message[:50]}...")
        
        # Send typing indicator
        await update.effective_chat.send_action("typing")
        
        try:
            # Get AI response via callback
            response = await self.on_message(user_message)
            
            # Send response with Markdown fallback
            async def send_with_fallback(text: str):
                """Try Markdown first, fall back to plain text on parse error."""
                try:
                    await update.message.reply_text(text, parse_mode="Markdown")
                except Exception:
                    # Markdown parse failed, send as plain text
                    await update.message.reply_text(text)
            
            # Split if too long (Telegram limit is 4096)
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    await send_with_fallback(response[i:i+4000])
            else:
                await send_with_fallback(response)
                
        except Exception as e:
            logger.error(f"Telegram handler error: {e}")
            await update.message.reply_text(f"❌ Fel: {str(e)}")


def init_telegram_service(on_message: Callable) -> TelegramService:
    """Initialize the global Telegram service instance."""
    global telegram_service
    telegram_service = TelegramService(on_message)
    return telegram_service
