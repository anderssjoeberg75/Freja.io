"""Weather skill package for Freja.io."""

# Section: Imports
from skills._core.skill_types import SkillManifest
from skills.weather.tools import register_tools


# Section: Skill Manifest
SKILL = SkillManifest(
    name="weather",
    description="Provides weather forecast retrieval via SMHI.",
    version="1.0.0",
    tools=["get_weather"],
)


# Section: Skill Registration Hook
def register(registry) -> None:
    """Register all tools provided by the weather skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
