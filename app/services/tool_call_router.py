"""Server-side tool call router for forwarding Gemini tool calls to an external gateway."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger


class ToolCallRouter:
    """Routes model tool calls to a configurable HTTP gateway with token auth."""

    def __init__(self) -> None:
        # The gateway host/port/token are read from server-side config only.
        self.host = settings.OPENCLOW_HOST
        self.port = settings.OPENCLOW_PORT
        self.scheme = settings.OPENCLOW_SCHEME
        self.path = settings.OPENCLOW_PATH
        self.token = settings.OPENCLOW_TOKEN
        self.timeout_seconds = settings.OPENCLOW_TIMEOUT_SECONDS
        self.retries = settings.OPENCLOW_RETRIES

    @property
    def enabled(self) -> bool:
        """Return True when minimum gateway settings are present."""
        return bool(self.host and self.path)

    @property
    def execute_url(self) -> str:
        """Build the target gateway URL from configured host/port/path."""
        if self.port:
            return f"{self.scheme}://{self.host}:{self.port}{self.path}"
        return f"{self.scheme}://{self.host}{self.path}"

    async def execute(self, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
        """
        Forward a tool execution request to the gateway and return the normalized result.

        If gateway configuration is missing, this falls back to a no-op result to keep
        the Gemini session working during local smoke tests.
        """
        if not self.enabled:
            logger.warning("Tool gateway disabled; returning no-op response for %s", tool_name)
            return {
                "ok": True,
                "tool": tool_name,
                "text": f"Tool gateway disabled. No-op executed for {tool_name}.",
            }

        payload = {
            "tool": tool_name,
            "arguments": tool_args,
        }

        headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        last_error: Exception | None = None

        for attempt in range(1, self.retries + 2):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    logger.info("Forwarding tool call %s to gateway (attempt %s)", tool_name, attempt)
                    response = await client.post(self.execute_url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                # Normalize output for Gemini's tool response payload.
                if isinstance(data, dict):
                    if "text" in data:
                        text = str(data.get("text"))
                    elif "result" in data:
                        text = str(data.get("result"))
                    else:
                        text = str(data)
                    return {"ok": True, "tool": tool_name, "text": text, "raw": data}

                return {"ok": True, "tool": tool_name, "text": str(data)}
            except Exception as exc:  # noqa: BLE001 - broad exception to preserve session stability.
                last_error = exc
                logger.error("Gateway tool call failed (%s/%s): %s", attempt, self.retries + 1, exc)
                if attempt <= self.retries:
                    await asyncio.sleep(min(1.5 * attempt, 4.0))

        return {
            "ok": False,
            "tool": tool_name,
            "text": f"Gateway call failed for {tool_name}: {last_error}",
        }
