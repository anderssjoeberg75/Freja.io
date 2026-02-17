"""pfSense skill package for Freja.io."""

from skills._core.skill_types import SkillManifest
from skills.pfsense.tools import register_tools


SKILL = SkillManifest(
    name="pfsense",
    description="Provides pfSense log analysis and anomaly alerting via pfrest API.",
    version="1.0.0",
    tools=["analyze_pfsense_logs"],
)


def register(registry) -> None:
    """Register all tools provided by the pfSense skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
