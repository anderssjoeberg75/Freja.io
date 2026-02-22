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
    
    import skills.scheduler.tools
    skills.scheduler.tools.register_tools(registry)

    import skills.github_sentinel
    skills.github_sentinel.register_tools(registry)

    import skills._core.basic_tools # Force register Basic Tools
    
    # Register the user profile update tool manually
    from pydantic import BaseModel, Field
    from typing import Optional
    class UpdateUserProfileArgs(BaseModel):
        session_id: str = Field(..., description="ID of the current session or user id, provided implicitly.")
        age: Optional[str] = Field(None, description="The user's age.")
        max_hr: Optional[str] = Field(None, description="The user's maximum heart rate.")
        weight_kg: Optional[str] = Field(None, description="The user's weight in kilograms.")
    
    from skills.user_profile.tools import update_user_profile_impl
    registry.register(
        name="tool_update_user_profile",
        description="Uppdaterar användarens profilinformation (ålder, maxpuls, vikt). Använd om användaren direkt indikerar att de väger ett visst antal kg, har en viss maxpuls etc.",
        args_schema=UpdateUserProfileArgs
    )(update_user_profile_impl)
        
    discover_and_register_skills(registry)
