from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_allowed_origins, settings


def test_get_allowed_origins_parses_and_trims(monkeypatch):
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", " http://a.com,https://b.com , ,http://c.local ")

    assert get_allowed_origins() == [
        "http://a.com",
        "https://b.com",
        "http://c.local",
    ]


def test_get_allowed_origins_handles_empty(monkeypatch):
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "")

    assert get_allowed_origins() == []


def test_get_allowed_origins_deduplicates_values(monkeypatch):
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "http://a.com,http://a.com, http://b.com ,http://a.com")

    assert get_allowed_origins() == ["http://a.com", "http://b.com"]
