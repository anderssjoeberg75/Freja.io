"""Roborock tool registrations and orchestration logic."""

from __future__ import annotations

# Section: Imports
import json
from typing import Any

from app.core.config import get_credential, settings
from app.services.tool_registry import ToolRegistry
from app.tools.definitions import (
    RoborockCleanRoomsInput,
    RoborockConfigure,
    RoborockDeviceInput,
    RoborockMapImageInput,
)
from skills.roborock.client import RoborockClient, RoborockClientError
from skills.roborock.storage import RoborockStorage


# Section: Shared helpers
def _get_user_id() -> str:
    """Resolve current user id used as credentials partition key."""
    configured = str(get_credential("USER_ID", settings.USER_ID) or "").strip()
    return configured or "default"


def _coerce_rooms(rooms: list[int] | str) -> list[int]:
    """Normalize room input into integer segment IDs."""
    if isinstance(rooms, list):
        parsed = [int(r) for r in rooms]
    else:
        parsed = [int(part.strip()) for part in rooms.split(",") if part.strip()]

    if not parsed:
        raise ValueError("rooms must include at least one room/segment id")
    return parsed


def _resolve_credentials(storage: RoborockStorage) -> tuple[str, str, str | None]:
    """Load and decrypt credentials for current user, if configured."""
    user_id = _get_user_id()
    record = storage.get_credentials(user_id)
    if not record:
        raise ValueError("Not logged in")
    password = storage.decrypt_password(record.encrypted_password)
    return record.email, password, record.device_id


def _resolve_device_id(storage: RoborockStorage, requested_device_id: str | None) -> str:
    """Resolve explicit device id or fallback to stored default."""
    if requested_device_id:
        return requested_device_id

    user_id = _get_user_id()
    record = storage.get_credentials(user_id)
    if not record or not record.device_id:
        raise ValueError("Device not found")
    return record.device_id


# Section: Registry hook
def register_tools(registry: ToolRegistry) -> None:
    """Register Roborock-related tools in the shared tool registry."""

    storage = RoborockStorage()
    client = RoborockClient()

    @registry.register(
        name="roborock_configure",
        description="Validate Roborock login credentials and store encrypted credentials plus default device.",
        args_schema=RoborockConfigure,
    )
    def roborock_configure(email: str, password: str, device_id: str | None = None) -> str:
        """Configure Roborock integration for the current user."""
        try:
            devices = client.list_devices(email=email, password=password)
        except RoborockClientError as exc:
            return str(exc)
        if not devices:
            return "Authentication succeeded but no devices were found on this account."

        selected = None
        if device_id:
            for device in devices:
                if device.get("device_id") == device_id:
                    selected = device
                    break
            if not selected:
                return "Device not found"
        else:
            selected = devices[0]
            device_id = str(selected.get("device_id") or "")

        storage.save_credentials(
            user_id=_get_user_id(),
            email=email,
            password=password,
            device_id=device_id,
            device_name=selected.get("name") if selected else None,
            device_model=selected.get("model") if selected else None,
        )

        return json.dumps(
            {
                "message": "Roborock configured successfully.",
                "default_device_id": device_id,
                "default_device_name": selected.get("name") if selected else None,
                "devices": devices,
            },
            ensure_ascii=False,
        )

    @registry.register(
        name="roborock_list_devices",
        description="List devices available to configured Roborock account.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_list_devices(device_id: str | None = None) -> str:
        """List Roborock devices for currently configured credentials."""
        del device_id
        email, password, _ = _resolve_credentials(storage)
        try:
            devices = client.list_devices(email=email, password=password)
        except RoborockClientError as exc:
            return str(exc)
        return json.dumps(devices, ensure_ascii=False)

    def _run_action(action: str, device_id: str | None, **extra: Any) -> str:
        """Run one Roborock action with shared auth/device resolution and error handling."""
        email, password, _ = _resolve_credentials(storage)
        resolved_device = _resolve_device_id(storage, device_id)
        try:
            result = client.run_action(email=email, password=password, device_id=resolved_device, action=action, **extra)
        except RoborockClientError as exc:
            return str(exc)
        return json.dumps(result, ensure_ascii=False)

    @registry.register(
        name="roborock_status",
        description="Get current status for a Roborock vacuum.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_status(device_id: str | None = None) -> str:
        return _run_action("status", device_id)

    @registry.register(
        name="roborock_start",
        description="Start cleaning on a Roborock vacuum.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_start(device_id: str | None = None) -> str:
        return _run_action("start", device_id)

    @registry.register(
        name="roborock_stop",
        description="Stop cleaning on a Roborock vacuum.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_stop(device_id: str | None = None) -> str:
        return _run_action("stop", device_id)

    @registry.register(
        name="roborock_pause",
        description="Pause cleaning on a Roborock vacuum.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_pause(device_id: str | None = None) -> str:
        return _run_action("pause", device_id)

    @registry.register(
        name="roborock_dock",
        description="Send Roborock vacuum back to dock (home).",
        args_schema=RoborockDeviceInput,
    )
    def roborock_dock(device_id: str | None = None) -> str:
        return _run_action("dock", device_id)

    @registry.register(
        name="roborock_rooms",
        description="List available room/segment IDs for Roborock room cleaning.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_rooms(device_id: str | None = None) -> str:
        return _run_action("rooms", device_id)

    @registry.register(
        name="roborock_clean_rooms",
        description="Start room/segment cleaning by room IDs.",
        args_schema=RoborockCleanRoomsInput,
    )
    def roborock_clean_rooms(device_id: str | None = None, rooms: list[int] | str = "") -> str:
        parsed_rooms = _coerce_rooms(rooms)
        return _run_action("clean_rooms", device_id, rooms=parsed_rooms)

    @registry.register(
        name="roborock_consumables",
        description="Get Roborock consumables status (brush/filter/sensors).",
        args_schema=RoborockDeviceInput,
    )
    def roborock_consumables(device_id: str | None = None) -> str:
        return _run_action("consumables", device_id)

    @registry.register(
        name="roborock_maps",
        description="List maps available for the Roborock device.",
        args_schema=RoborockDeviceInput,
    )
    def roborock_maps(device_id: str | None = None) -> str:
        return _run_action("maps", device_id)

    @registry.register(
        name="roborock_map_image",
        description="Generate Roborock map image output (PNG).",
        args_schema=RoborockMapImageInput,
    )
    def roborock_map_image(device_id: str | None = None, output_format: str = "png") -> str:
        if output_format.lower() != "png":
            raise ValueError("Only output_format='png' is currently supported")
        return _run_action("map_image", device_id, output_format=output_format.lower())
