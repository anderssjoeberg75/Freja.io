"""Cybersecurity skill package."""

from skills._core.skill_types import SkillManifest
from skills.cybersecurity.tools import register_tools

SKILL = SkillManifest(
    name="cybersecurity",
    description="Authorized defensive security assessment planning and reporting.",
    version="1.0.0",
    tools=[
        "cybersecurity_assessment_blueprint",
        "cybersecurity_generate_report",
    ],
)


def register(registry) -> None:
    """Register cybersecurity tools."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
