"""Fitbit skill package for Freja.io."""

from skills._core.skill_types import SkillManifest
from skills.fitbit.tools import register_tools


SKILL = SkillManifest(
    name="fitbit",
    description="Provides Fitbit health and activity reporting tools.",
    version="1.0.0",
    tools=["get_fitbit_health"],
)


def register(registry) -> None:
    """Register all tools provided by the Fitbit skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
