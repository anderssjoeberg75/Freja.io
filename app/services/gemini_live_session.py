"""Bridge between Freja WebSocket clients and Gemini Live API sessions."""

from __future__ import annotations

import asyncio
import base64
from collections import deque
from typing import Any, Awaitable, Callable

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import logger
from app.services.tool_call_router import ToolCallRouter

DownstreamCallback = Callable[[dict[str, Any]], Awaitable[None]]


class GeminiLiveSession:
    """Maintains one Gemini Live websocket session and forwards audio/video + tool events."""

    def __init__(self, *, on_downstream_event: DownstreamCallback) -> None:
        # API key is loaded from server config only to avoid key leakage to the frontend.
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing on backend")

        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY, http_options={"api_version": "v1alpha"})
        self.model = settings.GEMINI_LIVE_MODEL
        self.on_downstream_event = on_downstream_event
        self.tool_router = ToolCallRouter()

        # Bounded queues provide basic backpressure for incoming media streams.
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=64)
        self._video_queue: deque[bytes] = deque(maxlen=2)

        self._session_cm: Any = None
        self._session: Any = None
        self._running = False
        self._send_tasks: list[asyncio.Task[Any]] = []
        self._receive_task: asyncio.Task[Any] | None = None

    async def start(self) -> None:
        """Open Gemini Live session and start background sender/receiver loops."""
        tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="gateway_execute",
                        description="Execute an external action through Freja gateway.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "action": types.Schema(type=types.Type.STRING, description="Action/tool name"),
                                "arguments": types.Schema(type=types.Type.OBJECT, description="Action arguments"),
                            },
                            required=["action"],
                        ),
                    )
                ]
            )
        ]

        # Response modalities include both text and audio for multimodal interaction parity.
        live_config = {
            "response_modalities": ["AUDIO", "TEXT"],
            "tools": tools,
            "system_instruction": "You are Freja. Always answer in Swedish.",
        }

        self._session_cm = self.client.aio.live.connect(model=self.model, config=live_config)
        self._session = await self._session_cm.__aenter__()
        self._running = True

        await self.on_downstream_event({"type": "status", "status": "connected", "model": self.model})
        logger.info("Gemini live session connected (model=%s)", self.model)

        self._send_tasks = [
            asyncio.create_task(self._audio_sender_loop(), name="gemini-live-audio-sender"),
            asyncio.create_task(self._video_sender_loop(), name="gemini-live-video-sender"),
        ]
        self._receive_task = asyncio.create_task(self._receive_loop(), name="gemini-live-receive")

    async def stop(self) -> None:
        """Close all tasks and the upstream Gemini session safely."""
        self._running = False

        for task in self._send_tasks:
            task.cancel()
        self._send_tasks = []

        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None

        if self._session_cm:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error while closing Gemini live session: %s", exc)

        self._session = None
        await self.on_downstream_event({"type": "status", "status": "disconnected"})

    async def send_audio_chunk(self, pcm16k_b64: str) -> None:
        """Queue one upstream audio chunk (PCM16 mono 16kHz)."""
        chunk = base64.b64decode(pcm16k_b64)
        try:
            self._audio_queue.put_nowait(chunk)
        except asyncio.QueueFull:
            # Drop oldest data under pressure to favor low-latency conversational behavior.
            _ = self._audio_queue.get_nowait()
            self._audio_queue.put_nowait(chunk)

    async def send_video_frame(self, jpeg_b64: str) -> None:
        """Store latest JPEG frame for ~1 FPS upstream vision updates."""
        frame = base64.b64decode(jpeg_b64)
        self._video_queue.append(frame)

    async def _audio_sender_loop(self) -> None:
        """Continuously forwards buffered audio chunks to Gemini Live realtime input."""
        while self._running and self._session:
            data = await self._audio_queue.get()
            await self._session.send_realtime_input(
                audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
            )

    async def _video_sender_loop(self) -> None:
        """Sends the latest buffered video frame, paced by configured frame rate."""
        sleep_interval = 1.0 / max(settings.LIVE_FRAME_FPS, 0.1)
        while self._running and self._session:
            if self._video_queue:
                latest = self._video_queue.pop()
                self._video_queue.clear()
                await self._session.send_realtime_input(
                    video=types.Blob(data=latest, mime_type="image/jpeg")
                )
                await self.on_downstream_event({"type": "status", "status": "frame_sent"})
            await asyncio.sleep(sleep_interval)

    async def _receive_loop(self) -> None:
        """Receives model events (audio/text/tool calls) and forwards them to frontend."""
        assert self._session is not None
        try:
            async for response in self._session.receive():
                # Handle explicit tool calls emitted by the model.
                tool_call = getattr(response, "tool_call", None)
                if tool_call and getattr(tool_call, "function_calls", None):
                    await self._handle_tool_call(tool_call)

                server_content = getattr(response, "server_content", None)
                if not server_content:
                    continue

                model_turn = getattr(server_content, "model_turn", None)
                if not model_turn:
                    continue

                for part in getattr(model_turn, "parts", []) or []:
                    inline_data = getattr(part, "inline_data", None)
                    text = getattr(part, "text", None)

                    if inline_data and getattr(inline_data, "data", None):
                        audio_b64 = base64.b64encode(inline_data.data).decode("utf-8")
                        await self.on_downstream_event(
                            {
                                "type": "audio_chunk_down",
                                "mime_type": getattr(inline_data, "mime_type", "audio/pcm;rate=24000"),
                                "audio": audio_b64,
                            }
                        )

                    if text:
                        await self.on_downstream_event({"type": "transcript", "text": text})
        except asyncio.CancelledError:
            logger.debug("Gemini receive loop cancelled")
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini receive loop error: %s", exc, exc_info=True)
            await self.on_downstream_event({"type": "error", "message": str(exc)})

    async def _handle_tool_call(self, tool_call: Any) -> None:
        """Routes each tool call through HTTP gateway and returns result back to Gemini."""
        function_responses: list[types.FunctionResponse] = []

        for call in tool_call.function_calls:
            action = call.args.get("action") if isinstance(call.args, dict) else None
            arguments = call.args.get("arguments", {}) if isinstance(call.args, dict) else {}
            action_name = action or call.name

            await self.on_downstream_event(
                {
                    "type": "tool_call",
                    "name": action_name,
                    "args": arguments,
                }
            )

            result = await self.tool_router.execute(action_name, arguments if isinstance(arguments, dict) else {})

            await self.on_downstream_event(
                {
                    "type": "tool_result",
                    "name": action_name,
                    "result": result,
                }
            )

            function_responses.append(
                types.FunctionResponse(
                    name=call.name,
                    id=call.id,
                    response={"result": result.get("text", "")},
                )
            )

        if function_responses:
            await self._session.send_tool_response(function_responses=function_responses)
