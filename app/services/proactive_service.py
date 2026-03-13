import asyncio
import datetime

import pytz

from app.core.config import settings
from app.core.config import get_credential
from app.core.logging import logger


class ProactiveService:
    def __init__(self, sio):
        self.sio = sio
        self.running = False
        self.task = None

    async def start(self):
        if self.running:
            return
        self.running = True
        logger.info("Proactive service started")
        self.task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Proactive service stopped")

    async def _loop(self):
        last_briefing_date = await self._load_last_briefing_date()
        last_audit_date = None
        last_briefing_attempt_at = None
        last_skip_reason_date = None

        while self.running:
            try:
                tz_name = get_credential("TIMEZONE", settings.TIMEZONE) or settings.TIMEZONE
                try:
                    tz = pytz.timezone(tz_name)
                except Exception:
                    tz = pytz.UTC

                now = datetime.datetime.now(tz)
                today = now.date()

                target_hour_raw = get_credential("MORNING_BRIEFING_HOUR", 8)
                try:
                    target_hour = int(target_hour_raw)
                except (TypeError, ValueError):
                    logger.warning(
                        "Invalid MORNING_BRIEFING_HOUR=%s, defaulting to 8", target_hour_raw
                    )
                    target_hour = 8

                if target_hour < 0 or target_hour > 23:
                    logger.warning("MORNING_BRIEFING_HOUR out of range (%s), defaulting to 8", target_hour)
                    target_hour = 8

                catch_up_window_minutes = self._parse_int_setting(
                    "MORNING_BRIEFING_CATCH_UP_MINUTES",
                    fallback=720,
                    min_value=30,
                    max_value=1440,
                )
                minutes_since_target = ((now.hour * 60) + now.minute) - (target_hour * 60)

                should_send_briefing = (
                    last_briefing_date != today
                    and 0 <= minutes_since_target < catch_up_window_minutes
                )

                if should_send_briefing:
                    if last_briefing_attempt_at and (now - last_briefing_attempt_at).total_seconds() < 300:
                        await asyncio.sleep(30)
                        continue

                    last_briefing_attempt_at = now
                    sent = await self.send_morning_briefing()
                    if sent:
                        last_briefing_date = today
                        from app.core.database import save_db_setting
                        await save_db_setting("LAST_MORNING_BRIEFING_DATE", today.isoformat())
                    else:
                        logger.warning("Morning briefing attempt failed; will retry within window")
                elif last_skip_reason_date != today:
                    logger.info(
                        "Morning briefing not due yet (today=%s, last_sent=%s, now=%02d:%02d, target_hour=%s, catch_up_window_minutes=%s)",
                        today,
                        last_briefing_date,
                        now.hour,
                        now.minute,
                        target_hour,
                        catch_up_window_minutes,
                    )
                    last_skip_reason_date = today

                audit_target_hour = 12
                audit_window_minutes = 180
                minutes_since_audit = ((now.hour * 60) + now.minute) - (audit_target_hour * 60)

                should_run_audit = (
                    last_audit_date != today and 0 <= minutes_since_audit < audit_window_minutes
                )

                if should_run_audit:
                    last_audit_date = today
                    await self.run_daily_audit()

                await asyncio.sleep(30)

            except Exception as exc:
                logger.error(f"Proactive service error: {exc}")
                await asyncio.sleep(60)

    async def run_daily_audit(self):
        """Run the daily code audit."""
        logger.info("Starting scheduled daily code audit...")
        try:
            from skills.codex.tools import audit_code_impl

            result = await audit_code_impl()
            logger.info(f"Daily audit completed: {result[:100]}...")
        except Exception as exc:
            logger.error(f"Daily audit failed: {exc}")

    async def send_morning_briefing(self) -> bool:
        """Generate and send the daily morning briefing."""
        logger.info("Generating morning briefing")

        try:
            import json

            from app.core.database import get_db_prompts
            from app.core.dependencies import get_garmin, get_strava, get_withings
            from app.services.chat_service import shared_chat_service
            from app.services.telegram_service import telegram_service
            from skills.weather.core import get_weather

            if not telegram_service or not telegram_service.primary_chat_id:
                logger.warning("Morning briefing skipped: Telegram is not configured")
                return False

            context_parts = []

            try:
                weather = await get_weather()
                context_parts.append(f"WEATHER:\n{weather}")
            except Exception as exc:
                logger.error(f"Weather error: {exc}")

            try:
                garmin = get_garmin()
                if garmin:
                    loop = asyncio.get_event_loop()
                    health = await loop.run_in_executor(None, garmin.get_health_report)
                    if isinstance(health, dict) and not health.get("error"):
                        date_label = f"{health.get('date')} (Idag)" if health.get('is_today') else f"{health.get('date')} (Gårdagen)"
                        g_parts = [
                            f"- Datum: {date_label}",
                            f"- Steg: {health.get('steps', 0)} (Mål: {health.get('step_goal', 'N/A')})",
                            f"- Sömn: {health.get('sleep_hours', 'N/A')} (Poäng: {health.get('sleep_score', 'N/A')})",
                            f"- Body Battery nu: {health.get('body_battery_now', 'N/A')}",
                            f"- Vilopuls: {health.get('resting_heart_rate', 'N/A')}",
                            f"- HRV Status: {health.get('hrv_status', 'N/A')}",
                            f"- Stress (snitt): {health.get('stress_avg', 'N/A')}",
                            f"- Kalorier: {health.get('total_calories', 0)} kcal"
                        ]
                        context_parts.append("HEALTH (Garmin):\n" + "\n".join(g_parts))
                    elif isinstance(health, dict) and health.get("error"):
                        context_parts.append(
                            f"HEALTH (Garmin): Could not fetch data ({health.get('error')})"
                        )
                    else:
                        context_parts.append("HEALTH (Garmin): Could not fetch data.")
                else:
                    context_parts.append("HEALTH (Garmin): Service not initialized")
            except Exception as exc:
                logger.error(f"Garmin proactive error: {exc}")

            try:
                strava = get_strava()
                if strava:
                    activities = await strava.get_health_report(limit=30)
                    if isinstance(activities, list):
                        activity_summary = json.dumps(activities, ensure_ascii=False)
                        context_parts.append(f"RECENT TRAINING (Strava):\n{activity_summary}")
                    elif isinstance(activities, dict) and activities.get("error"):
                        context_parts.append(
                            f"RECENT TRAINING (Strava): Could not fetch recent activities ({activities['error']})."
                        )
                    else:
                        context_parts.append("RECENT TRAINING (Strava): Could not fetch recent activities.")
                else:
                    context_parts.append("RECENT TRAINING (Strava): Service not initialized")
            except Exception as exc:
                logger.error(f"Strava proactive error: {exc}")

            try:
                withings = get_withings()
                if withings:
                    loop = asyncio.get_event_loop()
                    withings_health = await loop.run_in_executor(None, withings.get_health_report)
                    if isinstance(withings_health, dict) and not withings_health.get("error"):
                        w_text = (
                            f"- Benmassa: {withings_health.get('bone_mass_kg', 'Okänt')} kg\n"
                            f"- Blodtryck: {withings_health.get('blood_pressure_systolic', 'N/A')}/{withings_health.get('blood_pressure_diastolic', 'N/A')} mmHg\n"
                            f"- Puls vid mätning: {withings_health.get('heart_rate_at_measurement', 'N/A')} bpm\n"
                            f"- Steg (Withings): {withings_health.get('steps_withings', 0)}\n"
                            f"- Kalorier (Withings): {withings_health.get('total_calories', 0)} kcal"
                        )
                        context_parts.append(f"BODY COMPOSITION (Withings):\n{w_text}")
                    elif isinstance(withings_health, dict) and withings_health.get("error"):
                        context_parts.append(f"BODY COMPOSITION (Withings): {withings_health['error']}")
                    else:
                        context_parts.append("BODY COMPOSITION (Withings): Could not fetch data.")
                else:
                    context_parts.append("BODY COMPOSITION (Withings): Service not initialized")
            except Exception as exc:
                logger.error(f"Withings proactive error: {exc}")

            context = "\n\n".join(context_parts)

            try:
                tz_name = get_credential("TIMEZONE", settings.TIMEZONE) or settings.TIMEZONE
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.UTC

            current_time_str = datetime.datetime.now(tz).strftime("%H:%M")

            prompts = await get_db_prompts()
            prompt_template = prompts.get(
                "MORNING_BRIEFING_PROMPT",
                (
                    "You are Freja. Current time is {time}. "
                    "Create a morning briefing in Swedish based on:\n{context}\n\n"
                    "IMPORTANT: You must include a specific section titled '🚴 Dagens Träningsråd'. "
                    "In this section, explicitly recommend a workout for today based on my recovery (Garmin Body Battery/Sleep) "
                    "and recent training load (Strava). "
                    "Do not just summarize what I did previously, tell me what to do TODAY."
                ),
            )

            prompt = prompt_template.replace("{time}", current_time_str).replace("{context}", context)
            session_id = f"proactive_morning_{datetime.datetime.now(tz).date()}"
            full_response = await shared_chat_service.run_proactive_task(session_id, prompt)

            if full_response:
                target_chat = telegram_service.primary_chat_id
                if target_chat:
                    # Save full report to file
                    import os
                    import subprocess
                    try:
                        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
                        os.makedirs(report_dir, exist_ok=True)
                        timestamp = datetime.datetime.now(tz).strftime("%Y%m%d_%H%M%S")
                        report_path = os.path.join(report_dir, f"morning_briefing_{timestamp}.md")
                        with open(report_path, "w", encoding="utf-8") as f:
                            f.write(f"# 🌅 Morgon-Briefing {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M')}\n\n")
                            f.write(full_response)
                        logger.info(f"Morning briefing report saved to {report_path}")
                    except Exception as exc:
                        logger.warning(f"Could not save briefing report: {exc}")
                        report_path = None

                    # Build short summary for Telegram (first ~1200 chars)
                    lines = full_response.strip().splitlines()
                    summary_lines = []
                    char_count = 0
                    for line in lines:
                        if char_count + len(line) > 1200:
                            summary_lines.append("_...se bifogad rapport för fullständig information._")
                            break
                        summary_lines.append(line)
                        char_count += len(line) + 1

                    short_summary = "\n".join(summary_lines)
                    await telegram_service.send_message(
                        f"🌅 *Morning Briefing*\n\n{short_summary}", chat_id=target_chat
                    )

                    # Send full report as file attachment
                    if report_path and os.path.exists(report_path):
                        await telegram_service.send_document(
                            report_path,
                            caption="📄 Komplett Morning Briefing",
                            chat_id=target_chat
                        )

                    logger.info(f"Morning briefing sent to {target_chat}")
                    return True
                else:
                    logger.warning("Morning briefing skipped: No primary chat ID found")
                    return False

            logger.warning("Morning briefing generation returned an empty response")
            return False

        except Exception as exc:
            logger.error(f"Error sending morning briefing: {exc}")
            return False

    async def trigger_briefing(self):
        """Manually trigger the briefing for testing."""
        await self.send_morning_briefing()

    async def _load_last_briefing_date(self):
        """Load last successful morning briefing date from settings table."""
        try:
            from app.core.database import get_db_settings
            db_settings = await get_db_settings()
            stored_date = (db_settings.get("LAST_MORNING_BRIEFING_DATE") or "").strip()
            if stored_date:
                return datetime.date.fromisoformat(stored_date)
        except Exception as exc:
            logger.warning("Could not load LAST_MORNING_BRIEFING_DATE: %s", exc)
        return None

    def _parse_int_setting(
        self,
        key: str,
        fallback: int,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        raw_value = get_credential(key, fallback)
        try:
            parsed = int(raw_value)
        except (TypeError, ValueError):
            logger.warning("Invalid %s=%s, defaulting to %s", key, raw_value, fallback)
            return fallback

        if min_value is not None and parsed < min_value:
            logger.warning("%s below minimum (%s), defaulting to %s", key, min_value, fallback)
            return fallback

        if max_value is not None and parsed > max_value:
            logger.warning("%s above maximum (%s), defaulting to %s", key, max_value, fallback)
            return fallback

        return parsed


proactive_service = None


def init_proactive_service(sio):
    global proactive_service
    proactive_service = ProactiveService(sio)
    return proactive_service
