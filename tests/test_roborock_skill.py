"""Unit tests for Roborock skill validation, storage encryption, and subprocess wrapper."""

from __future__ import annotations

# Section: Imports
import json
import subprocess

import pytest
from cryptography.fernet import Fernet

from app.tools.definitions import RoborockCleanRoomsInput
from skills.roborock.client import RoborockClient, RoborockClientError
from skills.roborock.storage import RoborockStorage
from skills.roborock.tools import _coerce_rooms


# Section: Input validation tests
def test_roborock_clean_rooms_accepts_list_or_csv() -> None:
    model_list = RoborockCleanRoomsInput(rooms=[16, 17])
    model_csv = RoborockCleanRoomsInput(rooms="16,17")

    assert model_list.rooms == [16, 17]
    assert model_csv.rooms == "16,17"
    assert _coerce_rooms(model_list.rooms) == [16, 17]
    assert _coerce_rooms(model_csv.rooms) == [16, 17]


def test_roborock_clean_rooms_rejects_empty_values() -> None:
    with pytest.raises(ValueError):
        _coerce_rooms("")


# Section: Storage encryption tests
def test_roborock_storage_encrypts_password(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_file = tmp_path / "roborock.db"
    monkeypatch.setenv("ROBOROCK_SECRET_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr("skills.roborock.storage.DB_PATH", str(db_file))

    storage = RoborockStorage()
    storage.save_credentials("u1", "user@example.com", "topsecret", "device-1", "S8", "roborock.s8")

    record = storage.get_credentials("u1")
    assert record is not None
    assert record.encrypted_password != "topsecret"
    assert storage.decrypt_password(record.encrypted_password) == "topsecret"


# Section: Subprocess wrapper tests
def test_roborock_client_calls_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    client = RoborockClient()

    def fake_run(*args, **kwargs):
        del args
        payload = json.loads(kwargs["input"])
        assert payload["action"] == "list_devices"
        return subprocess.CompletedProcess(
            args=["python"],
            returncode=0,
            stdout=json.dumps({"ok": True, "devices": [{"device_id": "abc"}]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    devices = client.list_devices("user@example.com", "secret")

    assert devices[0]["device_id"] == "abc"


def test_roborock_client_raises_on_bridge_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = RoborockClient()

    def fake_run(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess(args=["python"], returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RoborockClientError):
        client.list_devices("user@example.com", "secret")
