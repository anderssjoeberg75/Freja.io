"""Backward-compatible shim for legacy tool imports."""

# Section: Imports
from app.services.tool_registry import registry
from skills._core.skill_loader import discover_and_register_skills


def register_all_tools():
    """Explicitly register all skills and tools."""
    # Section: Legacy Compatibility Hook
    # Tool registration now happens via skills auto-discovery.
    import skills.codex  # Force load Codex skill
    skills.codex.register(registry) # Force register Codex tools

    import skills.google_calendar
    skills.google_calendar.register_tools(registry)

    import skills.deep_research
    skills.deep_research.register_tools(registry)
    
    import app.tools.scheduler_tools
    app.tools.scheduler_tools.register_tools(registry)

    import skills.github_sentinel
    skills.github_sentinel.register_tools(registry)

    import app.tools.basic_tools # Force register Basic Tools (Weather, WebSearch)
    discover_and_register_skills(registry)
