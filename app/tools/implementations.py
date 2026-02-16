"""Backward-compatible shim for legacy tool imports."""

# Section: Imports
from app.services.tool_registry import registry
from skills._core.skill_loader import discover_and_register_skills


# Section: Legacy Compatibility Hook
# Keep this module import-safe for any legacy path still importing app.tools.implementations.
# Tool registration now happens via skills auto-discovery.
<<<<<<< HEAD
=======
import skills.codex  # Force load Codex skill
skills.codex.register(registry) # Force register Codex tools

import skills.google_calendar
skills.google_calendar.register_tools(registry)

import app.tools.basic_tools # Force register Basic Tools (Weather, WebSearch)
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
discover_and_register_skills(registry)
