"""Garmin skill package for Freja.io."""

# Section: Imports
from skills._core.skill_types import SkillManifest
from skills.garmin.tools import register_tools


# Section: Skill Manifest
SKILL = SkillManifest(
    name="garmin",
    description="Provides Garmin health reporting tools.",
    version="1.0.0",
    tools=["get_garmin_health"],
)


# Section: Skill Registration Hook
def register(registry) -> None:
    """Register all tools provided by the Garmin skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
