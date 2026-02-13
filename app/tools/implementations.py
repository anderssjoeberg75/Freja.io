"""Backward-compatible shim for legacy tool imports."""

# Section: Imports
from app.services.tool_registry import registry
from skills._core.skill_loader import discover_and_register_skills


# Section: Legacy Compatibility Hook
# Keep this module import-safe for any legacy path still importing app.tools.implementations.
# Tool registration now happens via skills auto-discovery.
discover_and_register_skills(registry)
