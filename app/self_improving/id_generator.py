"""ID generation helpers for self-improving memory entries."""

from __future__ import annotations

from datetime import datetime, timezone
from random import randint
from threading import Lock


class EntryIDGenerator:
    """Generate robust IDs in TYPE-YYYYMMDD-XXX format with local process uniqueness guards."""

    _lock = Lock()
    _last_date = ""
    _sequence = 0

    PREFIX_MAP = {
        "learning": "LRN",
        "error": "ERR",
        "feature": "FEAT",
    }

    @classmethod
    def generate(cls, entry_type: str, randomize: bool = False) -> str:
        """Return a new ID with either sequential or randomized 3-digit suffix."""
        normalized = entry_type.strip().lower()
        if normalized not in cls.PREFIX_MAP:
            raise ValueError(f"Unsupported entry type: {entry_type}")

        prefix = cls.PREFIX_MAP[normalized]
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")

        with cls._lock:
            if randomize:
                suffix = randint(0, 999)
            else:
                if cls._last_date != date_part:
                    cls._last_date = date_part
                    cls._sequence = 0
                cls._sequence += 1
                suffix = cls._sequence

        return f"{prefix}-{date_part}-{suffix:03d}"



def iso_logged_timestamp() -> str:
    """Return an ISO-8601 timestamp in UTC for the Logged metadata field."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
