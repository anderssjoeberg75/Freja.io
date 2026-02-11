import json
from typing import Optional

from app.core.dependencies import get_garmin, get_strava
from app.core.logging import logger


def build_realtime_context() -> str:
    """Build realtime context payload from enabled providers."""
    context_parts: list[str] = []

    garmin_tool = get_garmin()
    if garmin_tool:
        try:
            health_data = garmin_tool.get_health_report()
            if health_data and not health_data.get("error"):
                context_parts.append(
                    f"GARMIN DATA:\n{json.dumps(health_data, indent=2, ensure_ascii=False)}"
                )
        except Exception as exc:
            logger.error("Garmin fetch error: %s", exc)

    strava_tool = get_strava()
    if strava_tool and hasattr(strava_tool, "cached_data") and strava_tool.cached_data:
        context_parts.append(
            f"STRAVA DATA:\n{json.dumps(strava_tool.cached_data, indent=2, ensure_ascii=False)}"
        )

    return "\n\n".join(context_parts)


def with_realtime_context(system_prompt: str, label: Optional[str] = None) -> str:
    """Append realtime context to a system prompt if data is available."""
    context = build_realtime_context()
    if not context:
        return system_prompt

    context_label = label or "REALTIME DATA"
    return f"{system_prompt}\n\n{context_label}:\n{context}"
