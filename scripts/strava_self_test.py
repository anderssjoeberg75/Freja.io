"""Local deterministic self-test for Freja.io Strava skill using fixtures."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Section: Ensure repository root is importable when script runs directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skills.strava import get_strava_command_processor


# Section: Script entrypoint that runs one analysis command end-to-end.
async def main() -> None:
    os.environ.setdefault("STRAVA_MOCK", "1")
    processor = get_strava_command_processor()
    fixture_name = os.environ.get("STRAVA_MOCK_FIXTURE", "mixed_run_ride")
    user_id = f"self-test-{fixture_name}"
    result = await processor.process_message(user_id, "analysera min strava senaste 30 dagar")

    if not result.handled or not result.response:
        raise RuntimeError("Strava self-test failed: command was not handled.")

    required_sections = ["Svar:", "Sammanfattning", "Trender", "Highlights", "Rekommendationer"]
    missing = [section for section in required_sections if section not in result.response]
    if missing:
        raise RuntimeError(f"Strava self-test failed: missing sections {missing}")

    print("Strava self-test passed.")
    print(result.response[:500])


if __name__ == "__main__":
    asyncio.run(main())
