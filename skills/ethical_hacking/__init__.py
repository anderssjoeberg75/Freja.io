"""Ethical hacking skill package for Freja.io."""

from skills._core.skill_types import SkillManifest
from skills.ethical_hacking.tools import register_tools


SKILL = SkillManifest(
    name="ethical_hacking",
    description="Provides authorized pentest reconnaissance and vulnerability checks for a target host or URL.",
    version="1.0.0",
    tools=["run_pentest_recon"],
)


def register(registry) -> None:
    """Register all tools provided by the ethical hacking skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
