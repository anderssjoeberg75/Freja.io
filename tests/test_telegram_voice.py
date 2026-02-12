import asyncio
from types import SimpleNamespace

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.telegram_service import TelegramService
from app.services.telegram_voice_handler import TelegramVoiceError


class DummyChat:
    def __init__(self):
        self.actions = []
        self.id = 123

    async def send_action(self, action):
        self.actions.append(action)


class DummyMessage:
    def __init__(self, text=None, voice=None):
        self.text = text
        self.voice = voice
        self.replies = []

    async def reply_text(self, text, parse_mode=None):
        self.replies.append((text, parse_mode))


class DummyVoiceHandler:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error

    async def transcribe_voice_message(self, voice):
        if self.error:
            raise self.error
        return self.text


async def _fake_callback(message):
    return f"Svar: {message}"


def test_voice_update_uses_same_text_pipeline():
    service = TelegramService(_fake_callback)
    service._voice_handler = DummyVoiceHandler(text="turn on the lights")

    chat = DummyChat()
    message = DummyMessage(voice=SimpleNamespace(file_id="abc", duration=2))
    update = SimpleNamespace(update_id=99, message=message, effective_chat=chat)

    asyncio.run(service._handle_voice_message(update, None))

    assert message.replies[-1][0] == "Svar: turn on the lights"


def test_voice_ffmpeg_or_transcription_error_returns_user_message():
    service = TelegramService(_fake_callback)
    service._voice_handler = DummyVoiceHandler(error=TelegramVoiceError("conversion failed"))

    chat = DummyChat()
    message = DummyMessage(voice=SimpleNamespace(file_id="abc", duration=2))
    update = SimpleNamespace(update_id=101, message=message, effective_chat=chat)

    asyncio.run(service._handle_voice_message(update, None))

    assert message.replies[-1][0] == "Jag kunde inte transkribera ljudet. Försök igen eller skriv kommandot som text."


def test_duplicate_update_is_ignored_once_processed():
    service = TelegramService(_fake_callback)

    chat = DummyChat()
    message = DummyMessage(text="Hej")
    update = SimpleNamespace(update_id=777, message=message, effective_chat=chat)

    asyncio.run(service._process_user_message(update, "Hej"))
    replies_after_first = len(message.replies)

    asyncio.run(service._process_user_message(update, "Hej"))

    assert len(message.replies) == replies_after_first
