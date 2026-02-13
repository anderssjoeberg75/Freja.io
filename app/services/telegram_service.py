"""
Telegram Bot Service for Freja.
Handles bidirectional messaging via Telegram text and voice messages.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
from pathlib import Path
from collections import OrderedDict
from typing import Awaitable, Callable, Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.core.database import get_db_settings
from app.services.speech_to_text import build_speech_to_text_provider
from app.services.telegram_voice_handler import TelegramVoiceError, TelegramVoiceHandler
from skills.strava import get_strava_command_processor
from skills.homeassistant import get_homeassistant_command_processor

logger = logging.getLogger(__name__)

# Global instance
telegram_service: Optional["TelegramService"] = None

# Rate limiting
_last_message_time: float = 0
RATE_LIMIT_SECONDS = 1.0

# Telegram retry/idempotency safeguards
PROCESSED_UPDATE_TTL_SECONDS = 600
PROCESSED_UPDATE_CACHE_SIZE = 5000


SELF_UPDATE_TRIGGER_PHRASES = (
    "uppdatera dig",
    "update yourself",
)

class TelegramService:
    """Telegram bot service for receiving and sending messages."""

    def __init__(self, on_message: Callable[[str], Awaitable[str]]):
        """
        Initialize Telegram service.

        Args:
            on_message: Async callback that receives user message and returns AI response.
        """
        self.on_message = on_message
        self.application: Optional[Application] = None
        self.bot_token: Optional[str] = None
        self.chat_ids: list[str] = []
        self._running = False

        # This in-memory cache prevents duplicate execution when Telegram retries updates.
        self._processed_updates: OrderedDict[int, float] = OrderedDict()

        # Voice handler is initialized at startup after token/config are loaded.
        self._voice_handler: Optional[TelegramVoiceHandler] = None

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
            # Build application.
            self.application = Application.builder().token(self.bot_token).build()

            # Build STT provider and voice pipeline once so each update can reuse it.
            stt_provider = build_speech_to_text_provider()
            self._voice_handler = TelegramVoiceHandler(bot_token=self.bot_token, stt_provider=stt_provider)

            # Add handlers.
            self.application.add_handler(CommandHandler("start", self._handle_start))
            # Register dedicated skill routes without affecting generic text handling.
            self.application.add_handler(CommandHandler("strava", self._handle_strava_command))
            self.application.add_handler(CommandHandler("ha", self._handle_homeassistant_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
            self.application.add_handler(MessageHandler(filters.VOICE, self._handle_voice_message))

            # Initialize and start polling.
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)

            self._running = True
            logger.info("Telegram bot started (Allowed Chat IDs: %s)", self.chat_ids)

        except Exception as e:
            logger.error("Failed to start Telegram bot: %s", e)

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
                logger.error("Error stopping Telegram bot: %s", e)

    @property
    def primary_chat_id(self) -> Optional[str]:
        """Return the first configured chat ID."""
        return self.chat_ids[0] if self.chat_ids else None

    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """
        Send a message to resolving chat IDs.

        Args:
            text: Message to send.
            chat_id: Specific chat ID to send to. If None, sends to all configured IDs.

        Returns:
            True if sent successfully to at least one chat.
        """
        if not self.application or not self.chat_ids:
            logger.warning("Telegram: Cannot send message, not configured")
            return False

        target_ids = [chat_id] if chat_id else self.chat_ids
        success = False

        for cid in target_ids:
            try:
                await self.application.bot.send_message(chat_id=int(cid), text=text, parse_mode="Markdown")
                success = True
            except Exception as e:
                logger.warning(f"Telegram Markdown send failed for {cid}, retrying as plain text: {e}")
                try:
                    await self.application.bot.send_message(chat_id=int(cid), text=text, parse_mode=None)
                    success = True
                except Exception as e2:
                    logger.error(f"Telegram send error for {cid}: {e2}")

        return success

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)
        logger.info("Telegram /start from chat %s", chat_id)

        welcome_msg = f"🤖 *Freja Online*\n\nDitt Chat ID: `{chat_id}`\n\n"

        if self.chat_ids and chat_id not in self.chat_ids:
            welcome_msg += "⛔ Du är inte behörig att använda denna bot."
        else:
            welcome_msg += "✅ Du är inloggad! Skriv ett meddelande så svarar jag."

        await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    async def _handle_strava_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /strava command by routing to Strava skill parser with chat-scoped user ID."""
        if not update.message or not update.effective_chat:
            return

        chat_id = str(update.effective_chat.id)
        message_text = (update.message.text or "").strip()
        processor = get_strava_command_processor()
        result = await processor.process_message(chat_id, message_text)

        if result.handled and result.response:
            await update.message.reply_text(result.response)
            return

        await update.message.reply_text("Svar:\nOkänt Strava-kommando.")


    async def _handle_homeassistant_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ha command by routing to Home Assistant skill parser."""
        if not update.message or not update.effective_chat:
            return

        chat_id = str(update.effective_chat.id)
        message_text = (update.message.text or "").strip()
        processor = get_homeassistant_command_processor()
        result = await processor.process_message(chat_id, message_text)

        if result.handled and result.response:
            await update.message.reply_text(result.response)
            return

        await update.message.reply_text("Svar:\nOkänt HA-kommando.")

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram text messages using the shared pipeline."""
        user_message = (update.message.text or "").strip()
        if not user_message:
            await update.message.reply_text("Jag kunde inte läsa meddelandet. Försök igen.")
            return

        await self._process_user_message(update, user_message)

    async def _handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Telegram voice messages by converting speech into the existing text pipeline."""
        if not update.message or not update.message.voice:
            return

        if not self._voice_handler:
            await update.message.reply_text(
                "Jag kunde inte transkribera ljudet. Försök igen eller skriv kommandot som text."
            )
            return

        try:
            # Show activity while we download/convert/transcribe the incoming voice payload.
            await update.effective_chat.send_action("typing")

            transcribed_text = await self._voice_handler.transcribe_voice_message(update.message.voice)
            if not transcribed_text:
                raise TelegramVoiceError("Empty transcription")

            logger.info("Telegram voice message transcribed successfully")
            await self._process_user_message(update, transcribed_text)

        except TelegramVoiceError as exc:
            logger.warning("Telegram voice handling error: %s", exc)
            await update.message.reply_text(
                "Jag kunde inte transkribera ljudet. Försök igen eller skriv kommandot som text."
            )
        except Exception as exc:
            logger.error("Unexpected Telegram voice handling error: %s", exc, exc_info=True)
            await update.message.reply_text(
                "Jag kunde inte transkribera ljudet. Försök igen eller skriv kommandot som text."
            )

    @staticmethod
    def _is_self_update_command(user_message: str) -> bool:
        """Return True when the message asks Freja to self-update from GitHub."""
        normalized = " ".join(user_message.casefold().split())
        return normalized in SELF_UPDATE_TRIGGER_PHRASES

    async def _run_self_update(self) -> tuple[bool, str]:
        """Run the repository self-update script and return execution status."""
        repo_root = Path(__file__).resolve().parents[2]
        script_path = repo_root / "scripts" / "self_update.sh"

        if not script_path.exists():
            return False, "Update script is missing."

        cmd = f"bash {shlex.quote(str(script_path))}"
        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=str(repo_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        output = (stdout or b"").decode("utf-8", errors="replace").strip()
        error_output = (stderr or b"").decode("utf-8", errors="replace").strip()

        if process.returncode == 0:
            return True, output or "Update completed."

        message_parts = ["Update failed."]
        if output:
            message_parts.append(output)
        if error_output:
            message_parts.append(error_output)
        return False, "\n".join(message_parts)

    async def _process_user_message(self, update: Update, user_message: str):
        """Shared execution pipeline for all user messages, including transcribed voice."""
        global _last_message_time

        if not update.message or not update.effective_chat:
            return

        # Idempotency check is performed first to avoid duplicate actions on retried updates.
        if self._is_duplicate_update(update.update_id):
            logger.info("Telegram duplicate update ignored: %s", update.update_id)
            return

        chat_id = str(update.effective_chat.id)

        # Check if message comes from authorized chat.
        if self.chat_ids and chat_id not in self.chat_ids:
            logger.warning("Telegram: Unauthorized chat %s", chat_id)
            await update.message.reply_text("⛔ Obehörig användare.")
            return

        # Rate limiting protects the callback execution pipeline from message bursts.
        current_time = time.time()
        if current_time - _last_message_time < RATE_LIMIT_SECONDS:
            await update.message.reply_text("⏳ Vänta lite innan du skickar nästa meddelande.")
            return
        _last_message_time = current_time

        logger.info("Telegram message accepted for processing")

        if self._is_self_update_command(user_message):
            await update.effective_chat.send_action("typing")
            await update.message.reply_text("Jag uppdaterar mig nu från GitHub och startar om tjänsten.")
            success, details = await self._run_self_update()
            if success:
                await update.message.reply_text("✅ Uppdatering klar. start.sh körs nu.")
            else:
                await update.message.reply_text(f"❌ Uppdateringen misslyckades.\n{details}")
            return

        # Try Strava skill parser first for natural-language triggers in Telegram text.
        strava_processor = get_strava_command_processor()
        strava_result = await strava_processor.process_message(chat_id, user_message)
        if strava_result.handled and strava_result.response:
            await update.message.reply_text(strava_result.response)
            return

        # Send typing indicator while the command/intent pipeline executes.
        await update.effective_chat.send_action("typing")

        try:
            # This callback is intentionally unchanged so voice and text execute identical logic.
            response = await self.on_message(user_message)

            async def send_with_fallback(text: str):
                """Try Markdown first, then fall back to plain text when parse fails."""
                try:
                    await update.message.reply_text(text, parse_mode="Markdown")
                except Exception:
                    await update.message.reply_text(text)

            # Split long outputs to stay below Telegram's message size limits.
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    await send_with_fallback(response[i : i + 4000])
            else:
                await send_with_fallback(response)

        except Exception as exc:
            logger.error("Telegram handler error: %s", exc)
            await update.message.reply_text(f"❌ Fel: {str(exc)}")

    def _is_duplicate_update(self, update_id: Optional[int]) -> bool:
        """Return True when the update was already processed recently."""
        if update_id is None:
            return False

        now = time.time()
        self._evict_processed_updates(now)

        if update_id in self._processed_updates:
            return True

        self._processed_updates[update_id] = now

        # Keep cache bounded even under sustained high traffic.
        while len(self._processed_updates) > PROCESSED_UPDATE_CACHE_SIZE:
            self._processed_updates.popitem(last=False)

        return False

    def _evict_processed_updates(self, now: float) -> None:
        """Evict old update IDs from the idempotency cache."""
        while self._processed_updates:
            oldest_update_id, processed_at = next(iter(self._processed_updates.items()))
            if now - processed_at < PROCESSED_UPDATE_TTL_SECONDS:
                break
            self._processed_updates.pop(oldest_update_id, None)


def init_telegram_service(on_message: Callable[[str], Awaitable[str]]) -> TelegramService:
    """Initialize the global Telegram service instance."""
    global telegram_service
    telegram_service = TelegramService(on_message)
    return telegram_service
