"""Roborock skill package for Freja.io."""

# Section: Imports
from skills._core.skill_types import SkillManifest
from skills.roborock.tools import register_tools


# Section: Skill Manifest
SKILL = SkillManifest(
    name="roborock",
    description="Provides Roborock vacuum configuration, status, and control tools.",
    version="1.0.0",
    tools=[
        "roborock_configure",
        "roborock_list_devices",
        "roborock_status",
        "roborock_start",
        "roborock_stop",
        "roborock_pause",
        "roborock_dock",
        "roborock_rooms",
        "roborock_clean_rooms",
        "roborock_consumables",
        "roborock_maps",
        "roborock_map_image",
    ],
)


# Section: Skill Registration Hook
def register(registry) -> None:
    """Register all tools provided by the Roborock skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
