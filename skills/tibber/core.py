"""Core Tibber helpers for hourly price and consumption analysis."""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

import requests

TIBBER_ENDPOINT = "https://api.tibber.com/v1-beta/gql"


class TibberConfigError(RuntimeError):
    """Raised when Tibber configuration is missing or invalid."""


def _get_token() -> str:
    token = os.getenv("TIBBER_API_TOKEN", "").strip()
    if not token:
        raise TibberConfigError("Missing Tibber API token. Set TIBBER_API_TOKEN.")
    return token


def _run_query_sync(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    token = _get_token()
    response = requests.post(
        TIBBER_ENDPOINT,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    errors = payload.get("errors") or []
    if errors:
        message = "; ".join(str(item.get("message", item)) for item in errors)
        raise RuntimeError(f"Tibber GraphQL error: {message}")

    return payload.get("data") or {}


def _to_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _extract_consumption_nodes(data: dict[str, Any], from_utc: datetime) -> list[dict[str, Any]]:
    homes = ((data.get("viewer") or {}).get("homes") or [])
    if not homes:
        return []

    consumption = (((homes[0].get("consumption") or {}).get("nodes")) or [])
    rows: list[dict[str, Any]] = []

    for node in consumption:
        from_raw = node.get("from")
        cost = node.get("cost")
        usage = node.get("consumption")
        if not from_raw or usage in (None, 0):
            continue

        ts = _to_datetime(from_raw)
        if ts < from_utc:
            continue

        rows.append(
            {
                "from": ts,
                "cost": float(cost or 0.0),
                "consumption": float(usage),
                "unit_price": float(cost or 0.0) / float(usage),
            }
        )

    return rows


def _extract_price_nodes(data: dict[str, Any], from_utc: datetime) -> list[dict[str, Any]]:
    homes = ((data.get("viewer") or {}).get("homes") or [])
    if not homes:
        return []

    today = ((((homes[0].get("currentSubscription") or {}).get("priceInfo") or {}).get("today")) or [])
    tomorrow = ((((homes[0].get("currentSubscription") or {}).get("priceInfo") or {}).get("tomorrow")) or [])

    rows: list[dict[str, Any]] = []
    for node in [*today, *tomorrow]:
        starts_at = node.get("startsAt")
        total = node.get("total")
        if not starts_at or total is None:
            continue

        ts = _to_datetime(starts_at)
        if ts < from_utc:
            continue

        rows.append(
            {
                "starts_at": ts,
                "total": float(total),
                "level": str(node.get("level") or "UNKNOWN"),
                "currency": str(node.get("currency") or ""),
            }
        )

    return rows


def _build_tips(consumption_rows: list[dict[str, Any]], price_rows: list[dict[str, Any]]) -> list[str]:
    tips: list[str] = []

    if consumption_rows:
        expensive = sorted(consumption_rows, key=lambda item: item["unit_price"], reverse=True)[:3]
        peaks = ", ".join(
            f"{row['from'].strftime('%Y-%m-%d %H:%M')} ({row['unit_price']:.2f}/kWh)"
            for row in expensive
        )
        tips.append(
            "Shift flexible usage (dishwasher, EV charging, laundry) away from your most expensive usage hours: "
            + peaks
        )

        by_hour: dict[int, list[float]] = defaultdict(list)
        for row in consumption_rows:
            by_hour[row["from"].hour].append(row["consumption"])

        avg_hour = {hour: mean(values) for hour, values in by_hour.items()}
        top_hours = sorted(avg_hour.items(), key=lambda item: item[1], reverse=True)[:3]
        if top_hours:
            tips.append(
                "Your highest average consumption hours are "
                + ", ".join(f"{hour:02d}:00" for hour, _ in top_hours)
                + ". Consider reducing standby loads and delaying heavy appliances in those windows."
            )

    if price_rows:
        cheapest = sorted(price_rows, key=lambda item: item["total"])[:3]
        windows = ", ".join(
            f"{row['starts_at'].strftime('%Y-%m-%d %H:%M')} ({row['total']:.2f})" for row in cheapest
        )
        tips.append(f"Best near-term price windows: {windows}. Schedule flexible usage there when possible.")

    if not tips:
        tips.append("No actionable tip could be generated because Tibber returned limited data.")

    return tips


def _format_report(consumption_rows: list[dict[str, Any]], price_rows: list[dict[str, Any]], days: int) -> str:
    lines = ["Tibber Energy Analysis", f"- Window: last {days} day(s)"]

    if consumption_rows:
        total_kwh = sum(item["consumption"] for item in consumption_rows)
        total_cost = sum(item["cost"] for item in consumption_rows)
        avg_price = total_cost / total_kwh if total_kwh else 0.0

        lines.extend(
            [
                "- Consumption summary:",
                f"  - Sampled hours: {len(consumption_rows)}",
                f"  - Total usage: {total_kwh:.2f} kWh",
                f"  - Total energy cost: {total_cost:.2f}",
                f"  - Weighted avg unit price: {avg_price:.3f}/kWh",
            ]
        )
    else:
        lines.append("- Consumption summary: No consumption data available in selected window.")

    if price_rows:
        all_prices = [item["total"] for item in price_rows]
        lines.extend(
            [
                "- Price summary:",
                f"  - Sampled hours: {len(price_rows)}",
                f"  - Min price: {min(all_prices):.3f}",
                f"  - Max price: {max(all_prices):.3f}",
                f"  - Avg price: {mean(all_prices):.3f}",
            ]
        )
    else:
        lines.append("- Price summary: No price data available in selected window.")

    lines.append("- Tips:")
    for tip in _build_tips(consumption_rows, price_rows):
        lines.append(f"  - {tip}")

    lines.append("- Note: Keep the final user-facing answer in Swedish.")
    return "\n".join(lines)


def _fetch_energy_analysis_sync(days: int) -> str:
    if days < 1 or days > 30:
        raise ValueError("days must be between 1 and 30")

    from_utc = datetime.now(tz=timezone.utc) - timedelta(days=days)

    consumption_query = """
    query FetchConsumption($last: Int!) {
      viewer {
        homes {
          consumption(resolution: HOURLY, last: $last) {
            nodes {
              from
              to
              cost
              unitPrice
              unitPriceVAT
              consumption
              consumptionUnit
            }
          }
        }
      }
    }
    """

    price_query = """
    query FetchPriceInfo {
      viewer {
        homes {
          currentSubscription {
            priceInfo {
              today {
                total
                currency
                startsAt
                level
              }
              tomorrow {
                total
                currency
                startsAt
                level
              }
            }
          }
        }
      }
    }
    """

    consumption_data = _run_query_sync(consumption_query, variables={"last": min(days * 24, 720)})
    price_data = _run_query_sync(price_query)

    consumption_rows = _extract_consumption_nodes(consumption_data, from_utc=from_utc)
    price_rows = _extract_price_nodes(price_data, from_utc=from_utc)

    return _format_report(consumption_rows, price_rows, days=days)


class TibberTool:
    """Wrapper class for Tibber API interactions."""
    
    async def get_energy_analysis(self, days: int = 7) -> str:
        return await get_tibber_energy_analysis(days)

    def get_energy_data_sync(self, days: int = 1) -> dict:
        """Fetch raw energy data for persistence."""
        from_utc = datetime.now(tz=timezone.utc) - timedelta(days=days)
        
        # We need a simpler query for raw data
        query = """
        query FetchRawConsumption($last: Int!) {
          viewer {
            homes {
              consumption(resolution: HOURLY, last: $last) {
                nodes {
                  from
                  cost
                  consumption
                }
              }
            }
          }
        }
        """
        data = _run_query_sync(query, variables={"last": days * 24})
        rows = _extract_consumption_nodes(data, from_utc=from_utc)
        
        if not rows:
            return {}
            
        total_kwh = sum(r["consumption"] for r in rows)
        total_cost = sum(r["cost"] for r in rows)
        
        return {
            "total_kwh": total_kwh,
            "total_cost": total_cost,
            "entries_count": len(rows),
            "date": rows[0]["from"].strftime("%Y-%m-%d") if rows else None
        }

async def get_tibber_energy_analysis(days: int = 7) -> str:
    """Fetch Tibber energy data and produce a concise analysis report."""
    return await asyncio.to_thread(_fetch_energy_analysis_sync, days)


__all__ = ["get_tibber_energy_analysis", "TibberConfigError", "TibberTool"]
