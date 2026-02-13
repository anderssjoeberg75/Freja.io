import asyncio
from types import SimpleNamespace

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.services.telegram_service as telegram_module
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


class DummyStravaResult:
    handled = False
    response = ""


class DummyStravaProcessor:
    async def process_message(self, chat_id, message):
        return DummyStravaResult()


def _stub_strava_processor():
    telegram_module.get_strava_command_processor = lambda: DummyStravaProcessor()



def test_voice_update_uses_same_text_pipeline():
    service = TelegramService(_fake_callback)
    _stub_strava_processor()
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
    _stub_strava_processor()

    chat = DummyChat()
    message = DummyMessage(text="Hej")
    update = SimpleNamespace(update_id=777, message=message, effective_chat=chat)

    asyncio.run(service._process_user_message(update, "Hej"))
    replies_after_first = len(message.replies)

    asyncio.run(service._process_user_message(update, "Hej"))

    assert len(message.replies) == replies_after_first


def test_self_update_trigger_phrase_is_detected_with_extra_spaces():
    assert TelegramService._is_self_update_command("  Uppdatera   dig  ") is True
    assert TelegramService._is_self_update_command("update yourself") is True
    assert TelegramService._is_self_update_command("uppdatera mig") is False


def test_self_update_command_executes_update_flow():
    service = TelegramService(_fake_callback)
    _stub_strava_processor()

    async def fake_run_self_update():
        return True, "Update completed and start.sh launched."

    service._run_self_update = fake_run_self_update

    telegram_module._last_message_time = 0
    chat = DummyChat()
    message = DummyMessage(text="uppdatera dig")
    update = SimpleNamespace(update_id=202, message=message, effective_chat=chat)

    asyncio.run(service._process_user_message(update, "uppdatera dig"))

    assert message.replies[0][0] == "Jag uppdaterar mig nu från GitHub och startar om tjänsten."
    assert message.replies[1][0] == "✅ Uppdatering klar. start.sh körs nu."
