"""Home Assistant skill package for Freja.io."""

from skills._core.skill_types import SkillManifest
from skills.homeassistant.homeassistant_skill import get_homeassistant_command_processor
from skills.homeassistant.tools import register_tools

SKILL = SkillManifest(
    name="homeassistant",
    description="Provides integration with Home Assistant.",
    version="1.0.0",
    tools=["homeassistant_control", "homeassistant_service"],
)

def register(registry) -> None:
    """Register all tools provided by the homeassistant skill."""
    register_tools(registry)

__all__ = ["SKILL", "get_homeassistant_command_processor", "register_tools", "register"]
