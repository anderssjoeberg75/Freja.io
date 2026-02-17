"""Core pfSense log analysis helpers powered by the pfrest API."""

from __future__ import annotations

import asyncio
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests


@dataclass(slots=True)
class PfSenseConfig:
    """Runtime configuration for pfSense API access."""

    base_url: str
    api_key: str
    verify_tls: bool


def _get_config() -> PfSenseConfig:
    base_url = os.getenv("PFSENSE_API_URL", "").strip().rstrip("/")
    api_key = os.getenv("PFSENSE_API_KEY", "").strip()
    verify_tls = os.getenv("PFSENSE_VERIFY_TLS", "true").strip().lower() not in {"0", "false", "no"}
    return PfSenseConfig(base_url=base_url, api_key=api_key, verify_tls=verify_tls)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    raw = value.strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw)
    except ValueError:
        for fmt in ("%b %d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(raw, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=datetime.now(tz=timezone.utc).year)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _classify_log_entry(entry: dict[str, Any]) -> str:
    for field in ("process", "program", "subsystem", "source", "service"):
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()

    message = str(entry.get("message") or entry.get("msg") or "").lower()
    if "blocked" in message or "deny" in message:
        return "firewall-block"
    if "login" in message or "auth" in message:
        return "authentication"
    if "error" in message or "fail" in message:
        return "error"
    return "unknown"


def _extract_log_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "logs", "rows", "items", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _summarize(entries: list[dict[str, Any]], lookback_minutes: int) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(minutes=lookback_minutes)

    categories: Counter[str] = Counter()
    severity: Counter[str] = Counter()
    anomalies: list[str] = []

    recent_events = 0
    historical_events = 0

    for entry in entries:
        category = _classify_log_entry(entry)
        categories[category] += 1

        level = str(entry.get("severity") or entry.get("level") or "info").lower().strip()
        severity[level] += 1

        timestamp = _parse_timestamp(entry.get("timestamp") or entry.get("time") or entry.get("date"))
        if timestamp and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        if timestamp and timestamp >= cutoff:
            recent_events += 1
        else:
            historical_events += 1

        message = str(entry.get("message") or entry.get("msg") or "")
        if "kernel panic" in message.lower() or "out of memory" in message.lower():
            anomalies.append(f"Critical pattern detected: {message[:140]}")

    if recent_events >= max(20, historical_events * 0.35):
        anomalies.append(
            "Event-rate spike detected in the most recent window "
            f"({recent_events} recent events vs {historical_events} older events)."
        )

    if severity.get("error", 0) + severity.get("critical", 0) > max(5, int(len(entries) * 0.2)):
        anomalies.append("High ratio of error/critical events in sampled logs.")

    sorted_categories = categories.most_common(5)
    sorted_severity = severity.most_common()

    return {
        "sampled_events": len(entries),
        "lookback_minutes": lookback_minutes,
        "recent_events": recent_events,
        "historical_events": historical_events,
        "top_categories": sorted_categories,
        "severity_distribution": sorted_severity,
        "anomalies": anomalies,
    }


def _format_report(summary: dict[str, Any]) -> str:
    lines = [
        "pfSense Log Report",
        f"- Sampled events: {summary['sampled_events']}",
        f"- Analysis window: last {summary['lookback_minutes']} minutes",
        f"- Recent events: {summary['recent_events']}",
        f"- Older events: {summary['historical_events']}",
        "- Top categories:",
    ]

    for category, count in summary["top_categories"]:
        lines.append(f"  - {category}: {count}")

    lines.append("- Severity distribution:")
    for level, count in summary["severity_distribution"]:
        lines.append(f"  - {level}: {count}")

    if summary["anomalies"]:
        lines.append("- Alerts:")
        for warning in summary["anomalies"]:
            lines.append(f"  - ⚠️ {warning}")
    else:
        lines.append("- Alerts: No anomalies detected in the sampled logs.")

    return "\n".join(lines)


def _fetch_logs_sync(limit: int) -> list[dict[str, Any]]:
    config = _get_config()
    if not config.base_url or not config.api_key:
        raise RuntimeError(
            "Missing pfSense API configuration. Set PFSENSE_API_URL and PFSENSE_API_KEY."
        )

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {config.api_key}",
            "Accept": "application/json",
        }
    )

    endpoints = [
        f"{config.base_url}/api/v2/status/log/system",
        f"{config.base_url}/api/v1/status/log/system",
        f"{config.base_url}/api/status/log/system",
    ]

    for endpoint in endpoints:
        response = session.get(endpoint, params={"limit": limit}, timeout=20, verify=config.verify_tls)
        if response.status_code == 404:
            continue
        response.raise_for_status()
        return _extract_log_entries(response.json())

    raise RuntimeError("Could not find a working pfSense system log endpoint in pfrest.")


async def analyze_pfsense_logs(limit: int = 200, lookback_minutes: int = 60) -> str:
    """Fetch pfSense logs and build a short anomaly report."""
    entries = await asyncio.to_thread(_fetch_logs_sync, limit)
    summary = _summarize(entries, lookback_minutes=lookback_minutes)
    return _format_report(summary)


__all__ = ["analyze_pfsense_logs", "_summarize"]
