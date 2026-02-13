"""Subprocess-based Roborock client wrapper with strict timeouts and sanitized errors."""

from __future__ import annotations

# Section: Imports
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class RoborockClientError(RuntimeError):
    """Raised when Roborock bridge operations fail."""


class RoborockClient:
    """Executes Roborock actions via a Python bridge process."""

    # Section: Initialization
    def __init__(self, timeout_seconds: int = 25) -> None:
        self.timeout_seconds = timeout_seconds
        self.bridge_path = Path(__file__).with_name("roborock_bridge.py")

    # Section: Internal process execution helper
    def _run_bridge(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute bridge script with JSON payload and parse JSON response."""
        cmd = [sys.executable, str(self.bridge_path)]
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RoborockClientError("Roborock request timed out") from exc
        except Exception as exc:
            raise RoborockClientError(f"Failed to start Roborock bridge: {exc}") from exc

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()[:500]
            raise RoborockClientError(f"Roborock bridge failed: {stderr or 'unknown error'}")

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RoborockClientError("Roborock bridge returned invalid JSON") from exc

        if not data.get("ok", False):
            raise RoborockClientError(data.get("error", "Unknown Roborock error"))

        return data

    # Section: Public bridge methods
    def list_devices(self, email: str, password: str) -> list[dict[str, Any]]:
        payload = {"action": "list_devices", "email": email, "password": password}
        result = self._run_bridge(payload)
        return result.get("devices", [])

    def run_action(self, email: str, password: str, device_id: str, action: str, **kwargs) -> dict[str, Any]:
        payload = {
            "action": action,
            "email": email,
            "password": password,
            "device_id": device_id,
            **kwargs,
        }
        return self._run_bridge(payload)
