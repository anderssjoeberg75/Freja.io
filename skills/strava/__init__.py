"""Strava skill package for Freja.io."""

# Section: Public skill helpers
# Import command processor so Telegram and API routes can use one shared integration entrypoint.
from skills.strava.strava_commands import get_strava_command_processor

__all__ = ["get_strava_command_processor"]
