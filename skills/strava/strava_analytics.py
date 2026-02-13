"""Deterministic analytics pipeline for Strava activity summaries."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Optional


@dataclass
class AnalysisResult:
    """Structured result containing report-ready sections."""

    summary: dict[str, Any]
    trends: dict[str, Any]
    highlights: dict[str, Any]
    insights: list[str]
    recommendations: list[str]


class StravaAnalytics:
    """Computes deterministic metrics and natural-language insights from activities."""

    # Section: Public analysis orchestrator.
    def analyze(self, activities: list[dict[str, Any]], days: int, activity_type: Optional[str]) -> AnalysisResult:
        recent = activities
        prev_window = []

        # Section: Window splitting for trend comparison.
        if activities:
            midpoint = max(1, len(activities) // 2)
            prev_window = activities[:midpoint]
            recent = activities[midpoint:]

        summary = self._build_summary(activities)
        trends = self._build_trends(recent, prev_window)
        highlights = self._build_highlights(activities)
        insights = self._build_insights(summary, trends, highlights, activity_type, days)
        recommendations = self._build_recommendations(summary, trends)

        return AnalysisResult(
            summary=summary,
            trends=trends,
            highlights=highlights,
            insights=insights,
            recommendations=recommendations,
        )

    # Section: Core aggregate metrics.
    def _build_summary(self, activities: list[dict[str, Any]]) -> dict[str, Any]:
        total_distance = sum(item.get("distance_m", 0.0) for item in activities)
        total_moving = sum(item.get("moving_time_s", 0) for item in activities)
        total_elevation = sum(item.get("elevation_gain_m", 0.0) for item in activities)
        count = len(activities)

        run_items = [a for a in activities if str(a.get("type", "")).lower() == "run"]
        ride_items = [a for a in activities if str(a.get("type", "")).lower() == "ride"]

        summary = {
            "count": count,
            "total_distance_m": total_distance,
            "total_moving_time_s": total_moving,
            "total_elevation_m": total_elevation,
            "avg_distance_m": (total_distance / count) if count else 0.0,
            "avg_run_pace_mps": self._avg_metric(run_items, "average_speed_mps"),
            "avg_ride_speed_mps": self._avg_metric(ride_items, "average_speed_mps"),
            "avg_hr": self._avg_hr(activities),
            "hr_samples": len([a for a in activities if a.get("average_heartrate") is not None]),
        }
        return summary

    def _build_trends(self, recent: list[dict[str, Any]], previous: list[dict[str, Any]]) -> dict[str, Any]:
        recent_distance = sum(item.get("distance_m", 0.0) for item in recent)
        previous_distance = sum(item.get("distance_m", 0.0) for item in previous)

        recent_speed = self._avg_metric(recent, "average_speed_mps")
        previous_speed = self._avg_metric(previous, "average_speed_mps")

        recent_hr = self._avg_hr(recent)
        previous_hr = self._avg_hr(previous)

        return {
            "distance_change_pct": self._pct_change(recent_distance, previous_distance),
            "speed_change_pct": self._pct_change(recent_speed or 0.0, previous_speed or 0.0),
            "hr_change_pct": self._pct_change(recent_hr or 0.0, previous_hr or 0.0),
        }

    def _build_highlights(self, activities: list[dict[str, Any]]) -> dict[str, Any]:
        if not activities:
            return {"longest": None, "fastest": None}

        longest = max(activities, key=lambda x: x.get("distance_m", 0.0))
        comparable_runs = [a for a in activities if str(a.get("type", "")).lower() == "run" and a.get("distance_m", 0) > 3000]
        fastest = max(comparable_runs, key=lambda x: x.get("average_speed_mps", 0.0), default=None)

        return {"longest": longest, "fastest": fastest}

    # Section: Coach-style insight generation (deterministic rule-based).
    def _build_insights(
        self,
        summary: dict[str, Any],
        trends: dict[str, Any],
        highlights: dict[str, Any],
        activity_type: Optional[str],
        days: int,
    ) -> list[str]:
        insights: list[str] = []
        label = activity_type or "alla aktiviteter"
        insights.append(f"Du har {summary['count']} pass registrerade för {label} de senaste {days} dagarna.")
        insights.append(f"Total volym är {summary['total_distance_m'] / 1000:.1f} km med {summary['total_elevation_m']:.0f} höjdmeter.")

        if summary["hr_samples"] == 0:
            insights.append("Pulssensor-data saknas i perioden, så intensitetsanalysen är begränsad.")
        else:
            insights.append(f"Medelpulsen i passen med pulsdata är {summary['avg_hr']:.0f} bpm.")

        if trends["distance_change_pct"] is not None:
            insights.append(f"Volymtrend: {trends['distance_change_pct']:+.1f}% jämfört med föregående jämförelsefönster.")
        if trends["speed_change_pct"] is not None:
            insights.append(f"Farttrend: {trends['speed_change_pct']:+.1f}% i snittfart mellan perioderna.")

        longest = highlights.get("longest")
        if longest:
            insights.append(
                f"Längsta passet var {longest.get('name', 'okänt pass')} på {longest.get('distance_m', 0.0) / 1000:.1f} km."
            )

        return insights[:8]

    def _build_recommendations(self, summary: dict[str, Any], trends: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []

        if trends.get("distance_change_pct") is not None and trends["distance_change_pct"] > 20:
            recommendations.append("Planera in minst en återhämtningsdag för att minska skaderisk vid snabb volymökning.")
        if summary.get("count", 0) < 3:
            recommendations.append("Öka till 3 pass per vecka för stabil progression över tid.")
        if trends.get("speed_change_pct") is not None and trends["speed_change_pct"] < -5:
            recommendations.append("Lägg till ett lätt kvalitetspass med teknik/fartlek för att vända farttrenden.")
        if not recommendations:
            recommendations.append("Fortsätt med nuvarande belastning och följ upp trend igen om en vecka.")

        return recommendations[:3]

    # Section: Small reusable math helpers.
    def _avg_metric(self, activities: list[dict[str, Any]], key: str) -> Optional[float]:
        values = [float(item.get(key, 0.0) or 0.0) for item in activities if item.get(key) is not None]
        return mean(values) if values else None

    def _avg_hr(self, activities: list[dict[str, Any]]) -> Optional[float]:
        values = [float(item["average_heartrate"]) for item in activities if item.get("average_heartrate") is not None]
        return mean(values) if values else None

    def _pct_change(self, current: float, previous: float) -> Optional[float]:
        if previous == 0:
            return None
        return ((current - previous) / previous) * 100.0
