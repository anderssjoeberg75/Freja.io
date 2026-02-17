"""Tibber skill package for Freja.io."""

from skills._core.skill_types import SkillManifest
from skills.tibber.tools import register_tools


SKILL = SkillManifest(
    name="tibber",
    description="Provides Tibber energy consumption and electricity price analysis with optimization tips.",
    version="1.0.0",
    tools=["get_tibber_energy_analysis"],
)


def register(registry) -> None:
    """Register all tools provided by the Tibber skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
