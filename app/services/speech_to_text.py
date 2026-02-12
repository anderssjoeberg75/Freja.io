"""Speech-to-text provider abstractions used by Telegram voice handling."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Protocol

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextError(Exception):
    """Raised when audio transcription fails in a user-facing flow."""


class SpeechToTextProvider(Protocol):
    """Protocol used to keep STT engines swappable without changing caller logic."""

    async def transcribe_audio(self, file_path: str, language: str = "sv") -> str:
        """Transcribe an audio file and return plain text."""


@dataclass(slots=True)
class DisabledSpeechToTextProvider:
    """Explicit provider that fails with a clear configuration message."""

    reason: str = "Speech-to-text provider is disabled."

    async def transcribe_audio(self, file_path: str, language: str = "sv") -> str:
        raise SpeechToTextError(self.reason)


@dataclass(slots=True)
class OpenAISpeechToTextProvider:
    """OpenAI Whisper-based provider implementation."""

    api_key: str
    timeout_seconds: float = 45.0

    async def transcribe_audio(self, file_path: str, language: str = "sv") -> str:
        # This call is intentionally strict so upstream code can safely handle empty outputs.
        client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout_seconds)

        try:
            with open(file_path, "rb") as audio_file:
                transcript = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text",
                )
        except Exception as exc:
            logger.error("OpenAI STT request failed: %s", exc)
            raise SpeechToTextError("OpenAI transcription failed") from exc

        text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
        if not text:
            raise SpeechToTextError("Transcription returned no text")

        return text


def build_speech_to_text_provider() -> SpeechToTextProvider:
    """Build an STT provider from settings with safe defaults."""
    configured_provider = (settings.STT_PROVIDER or "").strip().lower()
    resolved_provider = configured_provider

    # If provider is not explicitly configured, auto-enable OpenAI when an API key exists.
    if not resolved_provider:
        resolved_provider = "openai" if settings.OPENAI_API_KEY else "disabled"

    if resolved_provider == "openai":
        if not settings.OPENAI_API_KEY:
            return DisabledSpeechToTextProvider("OPENAI_API_KEY is missing for STT provider 'openai'.")
        return OpenAISpeechToTextProvider(api_key=settings.OPENAI_API_KEY)

    if resolved_provider == "disabled":
        return DisabledSpeechToTextProvider("Speech-to-text is disabled by configuration.")

    logger.warning("Unknown STT provider '%s', falling back to disabled provider.", resolved_provider)
    return DisabledSpeechToTextProvider(f"Unsupported STT provider: {resolved_provider}")
