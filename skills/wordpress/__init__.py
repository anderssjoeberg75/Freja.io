"""WordPress skill package for Freja.io."""

from skills._core.skill_types import SkillManifest
from skills.wordpress.tools import register_tools


SKILL = SkillManifest(
    name="wordpress",
    description="Provides a tool to publish or save draft articles to WordPress via REST API.",
    version="1.0.0",
    tools=["publish_wordpress_article"],
)


def register(registry) -> None:
    """Register all tools provided by the WordPress skill."""
    register_tools(registry)


__all__ = ["SKILL", "register"]
