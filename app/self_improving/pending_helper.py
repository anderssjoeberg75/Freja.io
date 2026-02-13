"""Helper for listing pending self-improving entries by area and priority."""

from __future__ import annotations

import json
from pathlib import Path

from app.self_improving.memory_logger import SelfImprovingMemoryLogger


def print_pending_entries(project_root: str | Path = ".") -> None:
    """Print pending entries grouped by area and priority as formatted JSON."""
    logger = SelfImprovingMemoryLogger(project_root=project_root)
    grouped = logger.list_pending()
    print(json.dumps(grouped, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    print_pending_entries()
