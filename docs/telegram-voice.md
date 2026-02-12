# Telegram Voice Message Support

This document describes the environment variables used by Telegram voice transcription.

## Environment variables

- `TELEGRAM_BOT_TOKEN`: Telegram bot token used for message polling and file download.
- `OPENAI_API_KEY`: OpenAI API key used when `STT_PROVIDER=openai`.
- `STT_PROVIDER`: Speech-to-text provider selector (`openai` or `disabled`). If empty, OpenAI is auto-selected when `OPENAI_API_KEY` exists.
- `STT_LANGUAGE_DEFAULT`: Default STT language code (`sv` by default).
- `MAX_VOICE_MB`: Maximum downloaded voice file size in MB (default `20`).
- `MAX_VOICE_SECONDS`: Maximum voice message duration in seconds based on Telegram metadata (default `120`).
- `TELEGRAM_VOICE_DOWNLOAD_TIMEOUT_SECONDS`: Timeout for Telegram file metadata/download requests.
- `TELEGRAM_STT_TIMEOUT_SECONDS`: Timeout for speech transcription requests.

## Runtime prerequisites

- `ffmpeg` must be installed and available in `PATH`.
- Telegram voice messages are downloaded as OGG/OPUS and converted to WAV before transcription.
