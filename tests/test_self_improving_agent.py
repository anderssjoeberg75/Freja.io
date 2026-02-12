"""Verification tests for markdown format, ID generation, and pending helper behavior."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from app.self_improving.id_generator import EntryIDGenerator
from app.self_improving.memory_logger import MemoryEntry, SelfImprovingMemoryLogger


class SelfImprovingAgentTests(unittest.TestCase):
    """Validate required formatting and behavior for self-improving logs."""

    def setUp(self) -> None:
        """Create an isolated temporary project root for each test case."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.logger = SelfImprovingMemoryLogger(project_root=self.root)

    def tearDown(self) -> None:
        """Clean up the temporary directory after each test run."""
        self.temp_dir.cleanup()

    def test_id_format_for_all_types(self) -> None:
        """Ensure generated IDs follow TYPE-YYYYMMDD-XXX exactly."""
        patterns = {
            "learning": r"^LRN-\d{8}-\d{3}$",
            "error": r"^ERR-\d{8}-\d{3}$",
            "feature": r"^FEAT-\d{8}-\d{3}$",
        }

        for entry_type, pattern in patterns.items():
            generated = EntryIDGenerator.generate(entry_type)
            self.assertRegex(generated, pattern)

    def test_markdown_entry_format_is_strict(self) -> None:
        """Ensure each stored entry contains heading, metadata, summary, and details sections."""
        self.logger.log_entry(
            MemoryEntry(
                entry_type="learning",
                title="Test learning",
                summary="A concise summary.",
                details="Detailed context for validation.",
                source="UserPromptSubmit",
                area="testing",
                priority="high",
            )
        )

        content = (self.root / ".learnings" / "LEARNINGS.md").read_text(encoding="utf-8")

        strict_pattern = re.compile(
            r"## LRN-\d{8}-\d{3} - Test learning\n"
            r"- Type: LEARNING\n"
            r"- Source: UserPromptSubmit\n"
            r"- Area: testing\n"
            r"- Priority: high\n"
            r"- Status: pending\n"
            r"- Logged: \d{4}-\d{2}-\d{2}T.*Z\n\n"
            r"### Summary\n"
            r"A concise summary\.\n\n"
            r"### Details\n"
            r"Detailed context for validation\.\n\n"
            r"---",
            re.MULTILINE,
        )
        self.assertRegex(content, strict_pattern)

    def test_pending_grouping_by_area_and_priority(self) -> None:
        """Ensure helper grouping returns pending entries in nested area/priority buckets."""
        self.logger.log_entry(
            MemoryEntry(
                entry_type="feature",
                title="Missing webhook retry setting",
                summary="Need retry controls.",
                details="Users request custom retry strategy.",
                source="UserPromptSubmit",
                area="integrations",
                priority="medium",
            )
        )

        grouped = self.logger.list_pending()
        self.assertIn("integrations", grouped)
        self.assertIn("medium", grouped["integrations"])
        self.assertTrue(any("Missing webhook retry setting" in item for item in grouped["integrations"]["medium"]))


if __name__ == "__main__":
    unittest.main()
