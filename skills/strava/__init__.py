"""Strava skill package for Freja.io."""

# Section: Public skill helpers
# Import command processor so Telegram and API routes can use one shared integration entrypoint.
from skills._core.skill_types import SkillManifest
from skills.strava.strava_commands import get_strava_command_processor
from skills.strava.tools import register_tools


# Section: Skill Manifest
SKILL = SkillManifest(
    name="strava",
    description="Provides Strava command processing and activity retrieval tools.",
    version="1.0.0",
    tools=["get_strava_activities"],
    telegram_commands=["/strava"],
)


# Section: Skill Registration Hook
def register(registry) -> None:
    """Register all tools provided by the Strava skill."""
    register_tools(registry)


__all__ = ["SKILL", "register", "get_strava_command_processor"]
