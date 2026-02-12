"""Structured markdown logger used by self-improving hooks and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.self_improving.id_generator import EntryIDGenerator, iso_logged_timestamp

EntryType = Literal["learning", "error", "feature"]


@dataclass
class MemoryEntry:
    """Represents one markdown entry with normalized metadata fields."""

    entry_type: EntryType
    title: str
    summary: str
    details: str
    source: str
    area: str = "general"
    priority: str = "medium"
    status: str = "pending"


class SelfImprovingMemoryLogger:
    """Writes and reads learning/error/feature entries under .learnings/."""

    FILES = {
        "learning": "LEARNINGS.md",
        "error": "ERRORS.md",
        "feature": "FEATURE_REQUESTS.md",
    }

    def __init__(self, project_root: str | Path = ".") -> None:
        """Initialize output paths and ensure baseline markdown files exist."""
        self.project_root = Path(project_root)
        self.learnings_dir = self.project_root / ".learnings"
        self.learnings_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_default_files()

    def _ensure_default_files(self) -> None:
        """Create markdown logs with stable headers if they are missing."""
        default_headers = {
            "LEARNINGS.md": "# Learnings Log\n\nStructured logs for user-correction learnings.\n\n",
            "ERRORS.md": "# Errors Log\n\nStructured logs for tool and runtime failures.\n\n",
            "FEATURE_REQUESTS.md": "# Feature Requests Log\n\nStructured logs for missing capability requests.\n\n",
            "PROJECT_MEMORY.md": "# Project Memory\n\nPromoted learnings that became permanent project memory.\n\n",
        }
        for filename, content in default_headers.items():
            target = self.learnings_dir / filename
            if not target.exists():
                target.write_text(content, encoding="utf-8")

    def log_entry(self, entry: MemoryEntry) -> str:
        """Append one entry to the proper markdown file and return created entry ID."""
        entry_id = EntryIDGenerator.generate(entry.entry_type)
        logged = iso_logged_timestamp()

        markdown_block = self._format_entry(
            entry_id=entry_id,
            entry_type=entry.entry_type,
            title=entry.title,
            source=entry.source,
            area=entry.area,
            priority=entry.priority,
            status=entry.status,
            logged=logged,
            summary=entry.summary,
            details=entry.details,
        )

        filepath = self.learnings_dir / self.FILES[entry.entry_type]
        with filepath.open("a", encoding="utf-8") as handle:
            handle.write(markdown_block)

        return entry_id

    @staticmethod
    def _format_entry(
        *,
        entry_id: str,
        entry_type: str,
        title: str,
        source: str,
        area: str,
        priority: str,
        status: str,
        logged: str,
        summary: str,
        details: str,
    ) -> str:
        """Enforce exact markdown entry structure (heading, metadata, summary, details)."""
        normalized_type = entry_type.upper()
        return (
            f"## {entry_id} - {title}\n"
            f"- Type: {normalized_type}\n"
            f"- Source: {source}\n"
            f"- Area: {area}\n"
            f"- Priority: {priority}\n"
            f"- Status: {status}\n"
            f"- Logged: {logged}\n\n"
            "### Summary\n"
            f"{summary.strip()}\n\n"
            "### Details\n"
            f"{details.strip()}\n\n"
            "---\n\n"
        )

    def promote_learning(self, learning_id: str, rationale: str = "") -> bool:
        """Promote a LEARNING entry into permanent memory and mark it promoted in source log."""
        learnings_path = self.learnings_dir / "LEARNINGS.md"
        content = learnings_path.read_text(encoding="utf-8")

        marker = f"## {learning_id} - "
        if marker not in content:
            return False

        chunks = content.split("## ")
        selected = ""
        rebuilt_chunks = [chunks[0]]

        for raw_chunk in chunks[1:]:
            chunk = "## " + raw_chunk
            if chunk.startswith(marker):
                selected = chunk
                if "- Status: pending" in chunk:
                    chunk = chunk.replace("- Status: pending", "- Status: promoted", 1)
                elif "- Status: reviewed" in chunk:
                    chunk = chunk.replace("- Status: reviewed", "- Status: promoted", 1)
            rebuilt_chunks.append(chunk)

        learnings_path.write_text("".join(rebuilt_chunks), encoding="utf-8")

        if not selected:
            return False

        project_memory_path = self.learnings_dir / "PROJECT_MEMORY.md"
        promoted_block = (
            f"## Promoted {learning_id}\n"
            f"- PromotedAt: {iso_logged_timestamp()}\n"
            f"- Rationale: {rationale or 'No rationale provided.'}\n\n"
            f"{selected.strip()}\n\n"
            "---\n\n"
        )
        with project_memory_path.open("a", encoding="utf-8") as handle:
            handle.write(promoted_block)

        return True

    def list_pending(self) -> dict[str, dict[str, list[str]]]:
        """Return pending entries grouped by area and then priority across all logs."""
        grouped: dict[str, dict[str, list[str]]] = {}

        for file_name in self.FILES.values():
            file_path = self.learnings_dir / file_name
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding="utf-8")
            entries = [f"## {chunk.strip()}" for chunk in content.split("## ") if chunk.strip()]
            for entry in entries:
                if "- Status: pending" not in entry:
                    continue

                heading = entry.splitlines()[0].strip().replace("## ", "")
                area = self._extract_metadata(entry, "Area") or "general"
                priority = self._extract_metadata(entry, "Priority") or "medium"

                grouped.setdefault(area, {}).setdefault(priority, []).append(heading)

        return grouped

    @staticmethod
    def _extract_metadata(entry_markdown: str, key: str) -> str:
        """Extract metadata values from one entry using simple line matching."""
        prefix = f"- {key}: "
        for line in entry_markdown.splitlines():
            if line.startswith(prefix):
                return line.replace(prefix, "", 1).strip()
        return ""
