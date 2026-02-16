"""Withings skill package for Freja.io."""

# Section: Imports
from skills._core.skill_types import SkillManifest
from skills.withings.tools import register_tools


# Section: Skill Manifest
SKILL = SkillManifest(
    name="withings",
    description="Provides Withings health reporting tools (weight, body composition).",
    version="1.0.0",
    tools=["get_withings_health"],
)


# Section: Skill Registration Hook
def register(registry) -> None:
    """Register all tools provided by the Withings skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
