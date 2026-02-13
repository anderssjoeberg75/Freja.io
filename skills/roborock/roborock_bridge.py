"""Bridge process for Roborock actions.

This script intentionally avoids logging sensitive payload content.
It reads a single JSON object from stdin and writes one JSON response to stdout.
"""

from __future__ import annotations

# Section: Imports
import asyncio
import json
import sys
from typing import Any


def _error(message: str, code: int = 1) -> None:
    """Write a structured error result and exit with non-zero code."""
    sys.stderr.write(message)
    sys.stderr.flush()
    raise SystemExit(code)


def _normalize_device(device: Any) -> dict[str, Any]:
    """Convert unknown library device model objects into simple dictionaries."""
    if isinstance(device, dict):
        return {
            "device_id": str(device.get("duid") or device.get("device_id") or ""),
            "name": device.get("name") or "Unknown",
            "model": device.get("model") or "Unknown",
        }

    return {
        "device_id": str(getattr(device, "duid", "") or getattr(device, "device_id", "")),
        "name": getattr(device, "name", "Unknown"),
        "model": getattr(device, "model", "Unknown"),
    }


async def _run(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute one Roborock action using python-roborock when available."""
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    action = (payload.get("action") or "").strip()

    if not email or not password:
        return {"ok": False, "error": "Authentication failed: missing email or password."}

    try:
        from roborock.api import RoborockApiClient
    except Exception:
        return {
            "ok": False,
            "error": (
                "Roborock dependency not installed. Install python-roborock in the runtime "
                "to enable Roborock tools."
            ),
        }

    try:
        client = RoborockApiClient(email=email, password=password)
        user_data = await client.pass_login()
        homes = await client.get_home_data(user_data)
        devices = homes.get("devices", []) if isinstance(homes, dict) else []
    except Exception:
        return {"ok": False, "error": "Authentication failed"}

    if action == "list_devices":
        normalized = [_normalize_device(d) for d in devices]
        return {"ok": True, "devices": normalized}

    device_id = str(payload.get("device_id") or "").strip()
    if not device_id:
        return {"ok": False, "error": "Device not found"}

    target = None
    for device in devices:
        normalized = _normalize_device(device)
        if normalized["device_id"] == device_id:
            target = normalized
            break

    if not target:
        return {"ok": False, "error": "Device not found"}

    # NOTE: Exact python-roborock command APIs vary by version.
    # We intentionally return a consistent unsupported message when a specific action is
    # unavailable so Freja can still surface a meaningful response.
    return {
        "ok": False,
        "error": "Roborock command bridge requires action-specific API wiring for this installed library version.",
    }


def main() -> None:
    """Program entrypoint with robust input/output handling."""
    raw = sys.stdin.read().strip()
    if not raw:
        _error("No JSON payload provided.")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _error("Invalid JSON payload.")

    result = asyncio.run(_run(payload))
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
