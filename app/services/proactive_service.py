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
        last_briefing_date = None
        last_audit_date = None
        last_briefing_attempt_at = None

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

                catch_up_window_minutes = 180
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
                    else:
                        logger.warning("Morning briefing attempt failed; will retry within window")

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
                    health = garmin.get_health_report()
                    if isinstance(health, dict) and not health.get("error"):
                        context_parts.append(f"HEALTH (Garmin):\n{json.dumps(health, ensure_ascii=False)}")
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
                    withings_health = withings.get_health_report()
                    if isinstance(withings_health, dict) and not withings_health.get("error"):
                        context_parts.append(
                            f"BODY COMPOSITION (Withings):\n{json.dumps(withings_health, ensure_ascii=False)}"
                        )
                    elif isinstance(withings_health, dict) and withings_health.get("error"):
                        context_parts.append(
                            f"BODY COMPOSITION (Withings): {withings_health['error']}"
                        )
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
            session_id = f"proactive_morning_{datetime.date.today()}"
            full_response = await shared_chat_service.run_proactive_task(session_id, prompt)

            if full_response:
                target_chat = telegram_service.primary_chat_id
                if target_chat:
                    await telegram_service.send_message(
                        f"🌅 **Morning Briefing**\n\n{full_response}", chat_id=target_chat
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


proactive_service = None


def init_proactive_service(sio):
    global proactive_service
    proactive_service = ProactiveService(sio)
    return proactive_service
