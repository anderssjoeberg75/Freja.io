"""WebSocket route for Freja live voice + vision streaming."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import logger
from app.services.gemini_live_session import GeminiLiveSession

router = APIRouter()


@router.websocket("/ws/live")
async def live_ws(websocket: WebSocket) -> None:
    """Bidirectional bridge between browser media events and Gemini Live responses."""
    await websocket.accept()
    logger.info("Live WS client connected")

    async def send_event(payload: dict[str, Any]) -> None:
        # Standardized JSON envelope sent to the browser for all downstream events.
        await websocket.send_text(json.dumps(payload))

    session: GeminiLiveSession | None = None

    try:
        session = GeminiLiveSession(on_downstream_event=send_event)
        await session.start()

        while True:
            raw = await websocket.receive_text()
            event = json.loads(raw)
            event_type = event.get("type")

            if event_type == "audio_chunk_up":
                audio_payload = event.get("audio", "")
                if audio_payload:
                    await session.send_audio_chunk(audio_payload)
            elif event_type == "video_frame_up":
                frame_payload = event.get("image", "")
                if frame_payload:
                    await session.send_video_frame(frame_payload)
            elif event_type == "ping":
                await send_event({"type": "pong"})
            else:
                await send_event({"type": "status", "status": "unknown_event", "event": event_type})
    except WebSocketDisconnect:
        logger.info("Live WS client disconnected")
    except Exception as exc:  # noqa: BLE001
        logger.error("Live WS error: %s", exc, exc_info=True)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:  # noqa: BLE001
            pass
    finally:
        if session:
            await session.stop()
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass
