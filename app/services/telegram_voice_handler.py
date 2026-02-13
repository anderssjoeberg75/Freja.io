"""Helpers for Telegram voice message ingestion and transcription."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from telegram import Voice

from app.core.config import settings
from app.services.speech_to_text import SpeechToTextError, SpeechToTextProvider

logger = logging.getLogger(__name__)


class TelegramVoiceError(Exception):
    """Domain error for Telegram voice processing failures."""


class TelegramVoiceHandler:
    """Download, convert and transcribe Telegram voice messages."""

    def __init__(self, bot_token: str, stt_provider: SpeechToTextProvider):
        self.bot_token = bot_token
        self.stt_provider = stt_provider
        self.max_voice_mb = max(1, settings.MAX_VOICE_MB)
        self.max_voice_seconds = max(1, settings.MAX_VOICE_SECONDS)
        self.default_language = (settings.STT_LANGUAGE_DEFAULT or "sv").strip() or "sv"
        self.download_timeout_seconds = settings.TELEGRAM_VOICE_DOWNLOAD_TIMEOUT_SECONDS
        self.transcribe_timeout_seconds = settings.TELEGRAM_STT_TIMEOUT_SECONDS

    async def transcribe_voice_message(self, voice: Voice, language: Optional[str] = None) -> str:
        """Fetch voice payload from Telegram and return transcribed text."""
        # Telegram includes duration metadata, so we reject overlong audio before any network work.
        if voice.duration and voice.duration > self.max_voice_seconds:
            raise TelegramVoiceError(
                f"Voice message is too long. Maximum allowed duration is {self.max_voice_seconds} seconds."
            )

        if not voice.file_id:
            raise TelegramVoiceError("Voice message has no file_id")

        requested_language = (language or self.default_language or "sv").strip()

        with tempfile.TemporaryDirectory(prefix="freja-telegram-voice-") as temp_dir:
            ogg_path = Path(temp_dir) / "voice.ogg"
            wav_path = Path(temp_dir) / "voice.wav"

            await self._download_voice_file(voice.file_id, ogg_path)
            await self._convert_ogg_to_wav(ogg_path, wav_path)

            try:
                transcript = await asyncio.wait_for(
                    self.stt_provider.transcribe_audio(str(wav_path), language=requested_language),
                    timeout=self.transcribe_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise TelegramVoiceError("Transcription timed out") from exc
            except SpeechToTextError as exc:
                raise TelegramVoiceError(str(exc)) from exc

            return transcript.strip()

    async def _download_voice_file(self, file_id: str, destination_path: Path) -> None:
        """Resolve Telegram file path and download binary payload with strict limits."""
        get_file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile"

        timeout = httpx.Timeout(self.download_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                get_file_response = await client.get(get_file_url, params={"file_id": file_id})
                get_file_response.raise_for_status()
            except Exception as exc:
                raise TelegramVoiceError("Failed to resolve Telegram voice file") from exc

            payload = get_file_response.json()
            if not payload.get("ok"):
                raise TelegramVoiceError("Telegram getFile returned failure")

            file_path = payload.get("result", {}).get("file_path")
            if not file_path:
                raise TelegramVoiceError("Telegram did not return file path")

            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"

            try:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    bytes_written = 0
                    max_bytes = self.max_voice_mb * 1024 * 1024
                    with open(destination_path, "wb") as output_file:
                        async for chunk in response.aiter_bytes():
                            if not chunk:
                                continue
                            bytes_written += len(chunk)
                            if bytes_written > max_bytes:
                                raise TelegramVoiceError(
                                    f"Voice file is too large. Maximum size is {self.max_voice_mb} MB."
                                )
                            output_file.write(chunk)
            except TelegramVoiceError:
                raise
            except Exception as exc:
                raise TelegramVoiceError("Failed to download Telegram voice file") from exc

    async def _convert_ogg_to_wav(self, source_path: Path, output_path: Path) -> None:
        """Convert OGG/OPUS voice payload into WAV accepted by transcription providers."""
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise TelegramVoiceError("ffmpeg is not installed on this host") from exc

        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.error(
                "ffmpeg conversion failed (exit=%s): %s %s",
                process.returncode,
                stdout.decode(errors="ignore"),
                stderr.decode(errors="ignore"),
            )
            raise TelegramVoiceError("Could not convert voice message audio")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise TelegramVoiceError("Converted audio file is empty")
