"""Telegram command parsing and response formatting for Strava skill."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from skills.strava.storage import StravaStorage
from skills.strava.strava_auth import StravaAuthManager
from skills.strava.strava_client import StravaClient
from skills.strava.strava_analytics import StravaAnalytics

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Container indicating if Strava command parser consumed a message."""

    handled: bool
    response: Optional[str] = None


class StravaCommandProcessor:
    """High-level orchestration for /strava commands and natural-language analysis triggers."""

    # Section: Dependency wiring and singleton-friendly constructor.
    def __init__(self) -> None:
        self.storage = StravaStorage()
        self.auth = StravaAuthManager(self.storage)
        self.client = StravaClient(self.auth, self.storage)
        self.analytics = StravaAnalytics()

    # Section: Main dispatch API used by Telegram service.
    async def process_message(self, user_id: str, text: str) -> CommandResult:
        normalized = text.strip()
        lowered = normalized.lower()

        if lowered.startswith("/strava"):
            return await self._handle_strava_command(user_id, normalized)

        if "analysera min strava" in lowered:
            return await self._handle_analysis_request(user_id, normalized)

        return CommandResult(handled=False)

    async def _handle_strava_command(self, user_id: str, text: str) -> CommandResult:
        parts = text.split()
        action = parts[1].lower() if len(parts) > 1 else "status"

        if action == "status":
            connected, record = self.auth.get_status(user_id)
            if not connected or not record:
                return CommandResult(True, "Svar:\nStrava är inte anslutet. Kör `/strava connect`.")

            expires = datetime.fromtimestamp(record.expires_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            updated = datetime.fromtimestamp(record.updated_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            return CommandResult(
                True,
                (
                    "Svar:\n"
                    "Strava är anslutet.\n"
                    f"Token uppdaterad: {updated}\n"
                    f"Token giltig till: {expires}"
                ),
            )

        if action == "connect":
            try:
                connect_url = self.auth.build_connect_url(user_id)
                manual_msg = (
                    "Svar:\n"
                    "Öppna länken för att ansluta Strava:\n"
                    f"{connect_url}\n\n"
                    "Om callback inte är aktiv: kopiera `code` från redirect-URL och kör\n"
                    "`/strava connect CODE_HERE`"
                )
                if len(parts) >= 3:
                    code = parts[2].strip()
                    await self.auth.exchange_code(user_id, code)
                    manual_msg = "Svar:\nStrava-koppling klar. Du kan nu skriva `analysera min strava senaste 30 dagar`."
                return CommandResult(True, manual_msg)
            except Exception as exc:
                return CommandResult(True, f"Svar:\nKunde inte ansluta Strava: {exc}")

        if action == "disconnect":
            self.auth.disconnect(user_id)
            return CommandResult(True, "Svar:\nStrava är nu frånkopplat för den här chatten.")

        return CommandResult(True, "Svar:\nOkänt Strava-kommando. Använd `/strava status`, `/strava connect` eller `/strava disconnect`.")

    async def _handle_analysis_request(self, user_id: str, text: str) -> CommandResult:
        days = self._extract_days(text)
        activity_type = self._extract_type(text)

        now = datetime.now(tz=timezone.utc)
        after = int((now - timedelta(days=days)).timestamp())
        before = int(now.timestamp())

        try:
            athlete = await self.client.get_athlete(user_id)
            athlete_id = int(athlete.get("id")) if athlete.get("id") else None
            stats = await self.client.get_athlete_stats(user_id, athlete_id) if athlete_id else {}
            activities = await self.client.fetch_activities(
                user_id=user_id,
                after_ts=after,
                before_ts=before,
                page_size=50,
                max_pages=6,
                activity_type=activity_type,
            )
        except Exception as exc:
            logger.error("Strava analysis failed: %s", exc)
            return CommandResult(True, f"Svar:\nKunde inte analysera Strava-data: {exc}")

        analysis = self.analytics.analyze(activities, days=days, activity_type=activity_type)
        response = self._format_analysis_response(analysis, days=days, athlete_name=athlete.get("firstname"), stats=stats)
        return CommandResult(True, response)

    # Section: Parsing helpers for message options.
    def _extract_days(self, text: str) -> int:
        match = re.search(r"(7|30|90)", text)
        if not match:
            return 30
        return int(match.group(1))

    def _extract_type(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if "run" in lowered:
            return "Run"
        if "ride" in lowered:
            return "Ride"
        if "walk" in lowered:
            return "Walk"
        return None

    # Section: Structured Telegram response rendering.
    def _format_analysis_response(self, analysis, days: int, athlete_name: Optional[str], stats: dict) -> str:
        summary = analysis.summary
        trends = analysis.trends
        highlights = analysis.highlights

        total_hours = summary["total_moving_time_s"] // 3600
        total_minutes = (summary["total_moving_time_s"] % 3600) // 60
        summary_lines = [
            f"Period: senaste {days} dagar",
            f"Antal pass: {summary['count']}",
            f"Total distans: {summary['total_distance_m'] / 1000:.1f} km",
            f"Total tid: {total_hours}h {total_minutes:02d}m",
            f"Snitt distans/pass: {summary['avg_distance_m'] / 1000:.1f} km",
            f"Total höjd: {summary['total_elevation_m']:.0f} m",
        ]

        if summary.get("avg_run_pace_mps"):
            pace = 1000 / summary["avg_run_pace_mps"] / 60
            summary_lines.append(f"Snitt tempo (run): {int(pace)}:{int((pace % 1) * 60):02d} min/km")
        if summary.get("avg_ride_speed_mps"):
            summary_lines.append(f"Snitt hastighet (ride): {summary['avg_ride_speed_mps'] * 3.6:.1f} km/h")

        trend_lines = [
            f"Distans: {self._fmt_pct(trends.get('distance_change_pct'))}",
            f"Fart: {self._fmt_pct(trends.get('speed_change_pct'))}",
            f"Pulsproxy: {self._fmt_pct(trends.get('hr_change_pct'))}",
        ]

        longest = highlights.get("longest")
        fastest = highlights.get("fastest")
        highlight_lines = [
            (
                f"Längsta pass: {longest.get('name', 'okänt')} ({longest.get('distance_m', 0) / 1000:.1f} km)"
                if longest
                else "Längsta pass: saknas"
            ),
            (
                f"Snabbaste jämförbara run: {fastest.get('name', 'okänt')} ({fastest.get('average_speed_mps', 0) * 3.6:.1f} km/h)"
                if fastest
                else "Snabbaste jämförbara run: saknas"
            ),
            f"YTD stats snapshot: run-count {((stats.get('all_run_totals') or {}).get('count', 'n/a'))}",
        ]

        rec_lines = [f"- {line}" for line in analysis.recommendations]
        insight_lines = [f"- {line}" for line in analysis.insights]
        title_name = athlete_name or "atlet"

        return (
            "Svar:\n"
            f"Strava-analys för {title_name}.\n\n"
            "Sammanfattning\n"
            + "\n".join(summary_lines)
            + "\n\nTrender\n"
            + "\n".join(trend_lines)
            + "\n\nHighlights\n"
            + "\n".join(highlight_lines)
            + "\n\nRekommendationer\n"
            + "\n".join(rec_lines)
            + "\n\nInsikter\n"
            + "\n".join(insight_lines)
        )

    def _fmt_pct(self, value: Optional[float]) -> str:
        if value is None:
            return "saknar jämförelsedata"
        return f"{value:+.1f}%"


# Section: Singleton factory to avoid repeated DB schema checks in hot paths.
_processor_singleton: Optional[StravaCommandProcessor] = None


def get_strava_command_processor() -> StravaCommandProcessor:
    """Return singleton command processor instance for Strava skill."""
    global _processor_singleton
    if _processor_singleton is None:
        _processor_singleton = StravaCommandProcessor()
    return _processor_singleton
